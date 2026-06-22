"""RAG 问答引擎（直连 DashScope HTTP，跳过 OpenAI SDK，qwen-turbo 快速路径）"""
import os
import sys
import time
import threading
import json
import hashlib

sys.path.insert(0, '/home/zwy1128/tour-guide-ai/backend')
from core.knowledge_base import KnowledgeBase

_DASHSCOPE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

def remove_emoji(text):
    import unicodedata
    out = []
    for ch in text:
        cp = ord(ch)
        cat = unicodedata.category(ch)
        if cat == 'So':
            continue
        if cat == 'Sk':
            continue
        if cat == 'Cf' and cp >= 0xFE00:
            continue
        out.append(ch)
    return ''.join(out).strip()

class RAGEngine:
    def __init__(self):
        self.kb = KnowledgeBase()
        self.model = os.getenv("RAG_MODEL", "qwen-plus")
        self.system_prompt = """你是灵山胜境景区的AI数字导游"小灵"。你必须严格仅根据【参考资料】回答游客的问题。
规则：
1. 回答内容只能从【参考资料】里摘取，绝不允许编造资料以外的内容。
2. 如果【参考资料】没有相关信息，直接说"抱歉，知识库中暂时没有关于这个问题的资料，我会继续学习的～"。
3. 回答 60-120 字，亲切自然。
4. 不要提及任何资料来源、文件名或依据（如不要说"根据xx..."）。"""
        self._answer_cache = {}
        self._cache_lock = threading.Lock()
        self._cache_max = 256
        self._session = None
        import requests
        self._requests = requests
        self._api_key = os.getenv("DASHSCOPE_API_KEY", "")

    def _http_call(self, messages):
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 200,
            "top_p": 0.9,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        if self._session is None:
            self._session = self._requests.Session()
        r = self._session.post(_DASHSCOPE_URL, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()

    def _cache_key(self, text: str) -> str:
        return hashlib.md5(text.strip().lower().encode("utf-8")).hexdigest()

    def answer(self, user_query: str) -> dict:
        ck = self._cache_key(user_query)
        with self._cache_lock:
            if ck in self._answer_cache:
                return self._answer_cache[ck]

        search_start = time.time()
        retrieved_docs = self.kb.search(user_query, k=5)
        search_time = time.time() - search_start

        context = "\n\n".join([f"[来源: {d['source']}]\n{d['content']}" for d in retrieved_docs])

        # 没有任何资料 → 直接返回固定回复，不调 LLM
        if not retrieved_docs:
            result = {
                "question": user_query,
                "answer": "抱歉，知识库中暂时没有关于这个问题的资料，我会继续学习的～",
                "sources": [],
                "no_context": True,
            }
            with self._cache_lock:
                if len(self._answer_cache) >= self._cache_max:
                    self._answer_cache.clear()
                self._answer_cache[ck] = result
            return result

        llm_start = time.time()
        try:
            resp = self._http_call([
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"【参考资料】\n{context}\n\n【用户问题】\n{user_query}"}
            ])
            answer = resp["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  [RAG] DashScope HTTP fail: {e}, fallback to short answer")
            answer = "抱歉，我暂时无法回答这个问题，请稍后再试。"
        llm_time = time.time() - llm_start

        sources = list(set([d['source'] for d in retrieved_docs]))

        print(f"  [RAG] model={self.model} search={search_time:.2f}s llm={llm_time:.2f}s")

        result = {
            "question": user_query,
            "answer": answer,
            "sources": sources,
        }
        with self._cache_lock:
            if len(self._answer_cache) >= self._cache_max:
                self._answer_cache.clear()
            self._answer_cache[ck] = result
        return result

    def clear_history(self):
        self._answer_cache.clear()
        return {"status": "ok"}

    def cache_hit_stats(self):
        return {"cached": len(self._answer_cache), "max": self._cache_max, "model": self.model}
