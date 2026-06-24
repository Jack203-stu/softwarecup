"""RAG 问答引擎 + AI智能路线规划 + 多层级知识库"""
import os
import sys

BASE_DIR = r"C:\Users\van\Desktop\aaa\t2\tour-guide-ai\backend"
sys.path.insert(0, BASE_DIR)

from core.route_recommender import RouteRecommender
from core.knowledge_base import KnowledgeBase
from core.data_analyzer import DataAnalyzer
from openai import OpenAI

# ====================== 多层级知识库路径配置 ======================
LIBRARY_ROOT = os.path.join(os.path.dirname(BASE_DIR), "data", "library")
LEVEL1_DIR = os.path.join(LIBRARY_ROOT, "level1")
LEVEL2_DIR = os.path.join(LIBRARY_ROOT, "level2")

os.makedirs(LEVEL1_DIR, exist_ok=True)
os.makedirs(LEVEL2_DIR, exist_ok=True)


def read_dir_content(folder_path):
    """读取指定文件夹下所有txt/md文件内容"""
    content = ""
    allow_suffix = (".txt", ".md")
    if not os.path.exists(folder_path):
        return content
    for fname in os.listdir(folder_path):
        file_path = os.path.join(folder_path, fname)
        if not os.path.isfile(file_path) or not fname.lower().endswith(allow_suffix):
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content += f"\n【{fname}】\n" + f.read()
        except:
            try:
                with open(file_path, "r", encoding="gbk") as f:
                    content += f"\n【{fname}】\n" + f.read()
            except:
                pass
    return content


def get_level1_content():
    return read_dir_content(LEVEL1_DIR)


def get_level2_content():
    return read_dir_content(LEVEL2_DIR)


class RAGEngine:
    def __init__(self):
        self.kb = KnowledgeBase()
        self.route_recomm = RouteRecommender()
        self.data_analyzer = DataAnalyzer()
        self.client = OpenAI(
            api_key="sk-7d9eb5d3d31d4eddaed244c54742f2b7",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = "qwen-plus"
        self.route_key = ["路线", "推荐路线", "游玩路线", "怎么玩", "游览攻略", "顺路游玩"]
        self.data_key = ["数据", "报告", "统计", "分析", "客流", "满意度", "游客", "景点排名"]
        
        # 缓存标志（用于刷新）
        self._cache_valid = False
        self._cached_level1 = ""
        self._cached_level2 = ""

    def refresh_knowledge(self):
        """手动刷新知识库，清除缓存，下次问答重新读取文件"""
        print("🔄 手动刷新知识库...")
        self._cache_valid = False
        self._cached_level1 = ""
        self._cached_level2 = ""
        print("✅ 知识库缓存已清除，下次问答将重新读取 LEVEL1/LEVEL2 文件")
        return {"status": "ok", "message": "知识库已刷新"}

    def _get_level1_with_cache(self):
        """带缓存的LEVEL1读取"""
        if not self._cache_valid:
            self._cached_level1 = get_level1_content()
            self._cached_level2 = get_level2_content()
            self._cache_valid = True
            print(f"📂 重新读取知识库: LEVEL1={len(self._cached_level1)}字符, LEVEL2={len(self._cached_level2)}字符")
        return self._cached_level1

    def _get_level2_with_cache(self):
        """带缓存的LEVEL2读取"""
        if not self._cache_valid:
            self._cached_level1 = get_level1_content()
            self._cached_level2 = get_level2_content()
            self._cache_valid = True
            print(f"📂 重新读取知识库: LEVEL1={len(self._cached_level1)}字符, LEVEL2={len(self._cached_level2)}字符")
        return self._cached_level2

    def answer(self, user_query: str):
        # 1. 数据分析
        if any(k in user_query for k in self.data_key):
            return {
                "question": user_query,
                "answer": self.data_analyzer.get_full_report(),
                "sources": ["景区Excel真实数据分析"]
            }

        # 2. 路线规划
        if any(k in user_query for k in self.route_key):
            spots = self.route_recomm.get_all_spots()
            prompt = f"""
身为灵山胜境导游，规划连贯顺路无折返游览路线，匹配用户需求，总时长60-120分钟，清晰列出序号景点及时长。
景点全部信息：{spots}
用户需求：{user_query}
"""
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return {
                "question": user_query,
                "answer": resp.choices[0].message.content,
                "sources": ["景点数据AI规划"]
            }

        # 3. 普通知识库问答
        docs = self.kb.search(user_query, k=5)
        official_content = "\n".join([d["content"] for d in docs])
        level1_content = self._get_level1_with_cache()
        level2_content = self._get_level2_with_cache()

        msg = f"""你是灵山胜境导游小灵，用亲切自然、像朋友聊天一样的口语和游客交流。

【内部规则 - 自己遵守，不要说出来】
1. 优先级：官方资料 > 一类补充文档 > 你的常识 > 二类轶闻文档
2. 一类补充文档里的内容直接回答，不要质疑
3. 二类轶闻文档里的内容用"据说"、"网上有人说"的话术
4. 绝对不要提"根据官方资料"、"根据优先级"、"根据文档"这类词
5. 不要解释信息来源，直接给答案

【参考信息】
{official_content}

{level1_content}

{level2_content}

【游客问题】
{user_query}

直接回答游客的问题，就像普通导游聊天一样，不要提规则、优先级、文档这些词。"""

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": msg}]
        )
        
        return {
            "question": user_query,
            "answer": resp.choices[0].message.content,
            "sources": [d["source"] for d in docs] if docs else ["官方资料 + 补充文档"]
        }