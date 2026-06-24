from docx import Document
import os

# 你的路径
BASE_DIR = r"C:\Users\van\Desktop\aaa\t2\tour-guide-ai"
DOC_PATH = os.path.join(BASE_DIR, "灵山胜境：历史、文化、景点特色与个性化游览指南.docx")
SAVE_DIR = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(SAVE_DIR, exist_ok=True)

# 读取 DOCX
print("🔍 读取官方文档...")
doc = Document(DOC_PATH)
lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
full_text = "\n\n".join(lines)

# 保存到 data/raw
out_path = os.path.join(SAVE_DIR, "lingshan_full_guide.txt")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(full_text)

print(f"✅ 文档转换完成！")
print(f"📄 总字数：{len(full_text)}")
print(f"📂 保存路径：{out_path}")