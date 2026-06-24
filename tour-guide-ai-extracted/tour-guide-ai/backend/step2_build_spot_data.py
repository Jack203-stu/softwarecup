from docx import Document
import os
import json

BASE = r"C:\Users\van\Desktop\aaa\t2\tour-guide-ai"
DOC_PATH = os.path.join(BASE, "灵山胜境 景点结构化数据集.docx")
OUT_PATH = os.path.join(BASE, "data", "spots.json")

print("🔍 读取官方结构化景点文档...")
doc = Document(DOC_PATH)
spots = []

for table in doc.tables:
    rows = table.rows
    if len(rows) < 2:
        continue
    # 跳过表头，从第二行开始
    for row in rows[1:]:
        cells = [c.text.strip() for c in row.cells]
        if len(cells) < 9:
            continue
        
        # 严格按真实表格列索引取值，从根源修正
        scenic_area = cells[0]
        spot_id = cells[1]
        spot_name = cells[2]       # 真正景点名称
        location = cells[3]        # 具体位置
        feature = cells[4]         # 建筑参数
        core_func = cells[5]       # 核心功能
        culture = cells[6]         # 文化内涵
        intro = cells[7]           # 详细介绍
        highlight = cells[8]       # 游玩亮点

        # 自动打标签，用于路线推荐
        tags = []
        if "佛教" in culture or "禅意" in intro:
            tags.append("佛教文化")
        if "历史" in intro or "千年" in intro:
            tags.append("历史人文")
        if "自然" in highlight or "山林" in location:
            tags.append("自然风光")
        if "亲子" in highlight or "互动" in highlight:
            tags.append("亲子游玩")
        if not tags:
            tags.append("休闲打卡")

        # 默认游览时长统一20分钟
        spot = {
            "name": spot_name,
            "spot_id": spot_id,
            "scenic_area": scenic_area,
            "location": location,
            "duration": 20,
            "tags": tags,
            "desc": highlight
        }
        spots.append(spot)

os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(spots, f, ensure_ascii=False, indent=2)

print(f"✅ 成功提取 {len(spots)} 个景点（已修复列索引）")
print(f"📂 保存到：{OUT_PATH}")