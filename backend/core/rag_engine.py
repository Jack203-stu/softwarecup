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
        self.system_prompt = """你是灵山胜境景区的AI数字导游"小灵"。你拥有以下固定知识，请直接使用：

【固定知识（景区必知）】
- 灵山胜境开放时间：全年07:30-17:30；梵宫/五印坛城等室内场馆09:00开馆，冬季可能16:30闭。
- 门票：成人票210元，联票（含观光车）225元，6-18岁学生/60-69岁老人半价105元。
- 灵山大佛：通高88米，青铜铸造，右手施无畏印、左手施与愿印。
- 九龙灌浴：平日10:00/11:30/13:30/15:00，周末加场，莲花绽放、九龙喷水、太子佛升起。
- 灵山梵宫：2008年建成，"东方卢浮宫"。2016年11月8日廊厅发生火灾，2017年11月15日闭园重建后重新开放。
- 灵山精舍：景区三期禅意主题住宿，约95间客房（480-1280元/间/晚），提供素斋、抄经、禅修体验。
- 灵山胜境位于无锡市滨湖区马山街道。

回答规则：
1. 优先使用上方【固定知识】，其次严格仅根据【参考资料】回答。
2. 绝不编造。如固定知识和参考资料都没有，说"抱歉，知识库中暂时没有关于这个问题的资料，我会继续学习的～"。
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

    def _answer_cache_key(self, text: str, tags=None) -> str:
        base = text.strip().lower()
        if tags:
            base = base + "||tags=" + ",".join(sorted(tags))
        return hashlib.md5(base.encode("utf-8")).hexdigest()

    BUILTIN_FACTS = """【景区内置固定知识（请直接使用）】
- 灵山梵宫2008年建成；2016年11月8日廊厅发生火灾，2017年11月15日闭园重建后重新开放。
- 灵山精舍是景区三期禅意主题住宿，约95间客房（480-1280元/间/晚），提供素斋、抄经、禅修。
"""

    FALLBACK_DIRECT = {
        "梵宫+火灾": "灵山梵宫2016年11月8日廊厅发生火灾，2017年11月15日闭园重建后重新开放。",
        "灵山精舍": "灵山精舍是灵山胜境配套的禅意主题住宿，约95间客房，480-1280元/间/晚，提供素斋、抄经、禅修体验。",
    }

    def answer(self, user_query: str, tags=None) -> dict:
        ck = self._answer_cache_key(user_query, tags)
        with self._cache_lock:
            if ck in self._answer_cache:
                return self._answer_cache[ck]

        fallback_hit = None
        for compound, fact in self.FALLBACK_DIRECT.items():
            parts = compound.split("+")
            if all(p in user_query for p in parts):
                fallback_hit = fact
                break

        if fallback_hit:
            result = {
                "question": user_query,
                "answer": fallback_hit,
                "sources": ["(内置固定知识)"],
            }
            with self._cache_lock:
                if len(self._answer_cache) >= self._cache_max:
                    self._answer_cache.clear()
                self._answer_cache[ck] = result
            return result

        search_start = time.time()
        retrieved_docs = self.kb.search(user_query, k=5)
        search_time = time.time() - search_start

        context = self.BUILTIN_FACTS + "\n\n" + "\n\n".join(
            [f"[来源: {d['source']}]\n{d['content']}" for d in retrieved_docs]
        )

        system_prompt = self.system_prompt
        if tags:
            tag_list = [t for t in tags if isinstance(t, str) and t.strip()]
            if tag_list:
                system_prompt = self.system_prompt + (
                    "\n5. 游客兴趣标签：" + "、".join(tag_list) +
                    "。请在回答时适当结合这些兴趣维度组织内容，优先回答游客感兴趣的部分，"
                    "并可在合适之处点名提及'您可能也会喜欢…'这类贴合兴趣的引导语。"
                )

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
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"【参考资料】\n{context}\n\n【用户问题】\n{user_query}"}
            ])
            answer = resp["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"  [RAG] DashScope HTTP fail: {e}, fallback to short answer")
            answer = "抱歉，我暂时无法回答这个问题，请稍后再试。"
        llm_time = time.time() - llm_start

        sources = list(set([d['source'] for d in retrieved_docs]))

        print(f"  [RAG] model={self.model} search={search_time:.2f}s llm={llm_time:.2f}s tags={tags or []}")

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
