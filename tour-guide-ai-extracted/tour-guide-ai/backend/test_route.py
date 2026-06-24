from core.route_recommender import RouteRecommender
from core.knowledge_base import KnowledgeBase
from core.data_analyzer import DataAnalyzer
from openai import OpenAI
import os

# ====================== 分两类文档读取逻辑 ======================
# 根目录
LIBRARY_ROOT = os.path.join(os.path.dirname(__file__), "..", "data", "library")
# 一类文档：高优先级（仅次于官方知识库，强制采信）
LEVEL1_DIR = os.path.join(LIBRARY_ROOT, "level1")
# 二类文档：趣味轶闻（低优先级，传闻口吻）
LEVEL2_DIR = os.path.join(LIBRARY_ROOT, "level2")

# 自动创建文件夹
os.makedirs(LEVEL1_DIR, exist_ok=True)
os.makedirs(LEVEL2_DIR, exist_ok=True)

def read_dir_content(folder_path):
    """读取指定文件夹下所有txt/md内容"""
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
                content += f"\n【文档：{fname}】\n" + f.read()
        except:
            try:
                with open(file_path, "r", encoding="gbk") as f:
                    content += f"\n【文档：{fname}】\n" + f.read()
            except:
                pass
    return content

# 读取两类文档
def get_all_library_content():
    level1 = read_dir_content(LEVEL1_DIR)
    level2 = read_dir_content(LEVEL2_DIR)
    # 顺序：一类在前，二类在后，保证优先级
    return level1 + level2
# ========================================================

# 全局初始化（原样保留）
rec = RouteRecommender()
all_spots = rec.get_all_spots()
kb = KnowledgeBase()
analyzer = DataAnalyzer()

client = OpenAI(
    api_key="sk-7d9eb5d3d31d4eddaed244c54742f2b7",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

route_words = ["路线","推荐路线","游玩路线","怎么玩","游览攻略","顺路游玩","亲子游玩路线","历史游玩路线"]
data_words = ["数据","报告","统计","分析","客流","游客","满意度","景点排名"]

print("=" * 60)
print("🧭 灵山综合测试：知识问答 + 路线规划 + 数据分析【已支持双分类文档】")
print("普通问题直接问答，提路线规划行程，exit退出")
print("=" * 60)

while True:
    user_text = input("\n你：").strip()
    if user_text.lower() in ["exit","quit","q"]:
        print("👋 结束测试")
        break
    if not user_text:
        continue

    # 数据分析（原样保留）
    if any(word in user_text for word in data_words):
        print("\n📊 景区数据分析报告：")
        print(analyzer.get_full_report())
        continue

    # 路线规划（原样保留）
    need_route = any(word in user_text for word in route_words)
    if need_route:
        prompt = f"""
你是灵山胜境导游，规划连续顺路不走回头路的游览路线，控制总时长60-120分钟，简洁列出序号+景点+时长。
全部景点数据：{all_spots}
用户需求：{user_text}
"""
        res = client.chat.completions.create(model="qwen-plus",messages=[{"role":"user","content":prompt}])
        print("\n🤖导游解答：")
        print(res.choices[0].message.content)
    else:
        # 拼接内容：官方知识库 → 一类文档 → 二类文档
        docs = kb.search(user_text, k=4)
        kb_context = "\n".join([d["content"] for d in docs])
        library_content = get_all_library_content()
        full_context = kb_context + library_content

        # 更新提示词：明确两类文档规则
        msg = f"""你是灵山胜境导游小灵，用亲切自然的口语和游客交流。
规则：
1. 采信优先级：景区官方资料 > 一类补充文档 > 二类轶闻文档，严格按优先级作答，不使用自身知识库内容。
2. 一类文档内容为有效正式信息，必须如实完整采纳、正常讲解。
3. 二类文档属于趣味轶闻内容，统一使用 据说、网上有人说、野史记载、有传言称 这类话术表述。
4. 所有资料中没有对应内容，就礼貌表示不清楚。
5. 全程不要提及资料、文档、文件来源，不评判内容真假。

参考资料：{full_context}
游客问题：{user_text}"""

        res = client.chat.completions.create(
            model="qwen-plus",
            messages=[{"role":"user","content":msg}]
        )
        print("\n🤖导游解答：")
        print(res.choices[0].message.content)