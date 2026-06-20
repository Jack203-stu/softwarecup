"""RAG 问答引擎"""
import os
import sys
import time
sys.path.insert(0, '/home/zwy1128/tour-guide-ai/backend')
from core.knowledge_base import KnowledgeBase
from openai import OpenAI


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
        self.client = OpenAI(
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = "qwen-plus"
        self.system_prompt = """你是灵山胜境景区的AI数字导游"小灵"。热情亲切。仅根据参考资料回答，不要编造。回答60-120字，简洁明了。"""
    
    def answer(self, user_query: str) -> dict:
        search_start = time.time()
        retrieved_docs = self.kb.search(user_query, k=3)
        search_time = time.time() - search_start
        
        context = "\n\n".join([f"[来源: {d['source']}]\n{d['content']}" for d in retrieved_docs])
        
        llm_start = time.time()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"【参考资料】\n{context}\n\n【用户问题】\n{user_query}"}
            ],
            temperature=0.3,
            max_tokens=200,
            top_p=0.9
        )
        llm_time = time.time() - llm_start
        
        print(f"  [RAG] Search: {search_time:.2f}s, LLM: {llm_time:.2f}s")
        
        return {
            "question": user_query,
            "answer": response.choices[0].message.content,
            "sources": list(set([d['source'] for d in retrieved_docs])),
        }

    def clear_history(self):
        """清除对话历史"""
        self.history = []
        return {"status": "ok"}
    
