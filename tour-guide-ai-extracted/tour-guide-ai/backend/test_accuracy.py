"""准确率自动化测试"""
import sys, json
sys.path.insert(0, '/home/zwy/tour-guide-ai/backend')
from core.rag_engine import RAGEngine

test_questions = [
    {"q": "灵山大佛有多高？", "keywords": ["101.5米", "79米", "青铜"]},
    {"q": "灵山胜境在哪里？", "keywords": ["无锡", "太湖", "马山"]},
    {"q": "门票多少钱？", "keywords": ["210元", "105", "半价"]},
    {"q": "灵山大佛什么时候开光的？", "keywords": ["1997", "11月15日"]},
    {"q": "远香堂在哪？", "keywords": ["不在", "没有", "资料"]},  # 应拒答
    {"q": "九龙灌浴是哪年建的？", "keywords": ["2003"]},
    {"q": "灵山梵宫什么时候开放？", "keywords": ["2009", "1月1日"]},
    {"q": "灵山胜境是几A景区？", "keywords": ["5A", "AAAAA"]},
    {"q": "小飞虹是什么？", "keywords": ["不在", "没有", "资料"]},  # 拙政园景点
    {"q": "推荐一条游览路线", "keywords": ["路线", "小时", "入口"]},
]

engine = RAGEngine()
correct = 0
results = []

for i, item in enumerate(test_questions):
    result = engine.answer(item['q'])
    answer = result['answer']
    # 简单关键词匹配
    hit = any(kw in answer for kw in item['keywords'])
    if hit:
        correct += 1
        status = "✅"
    else:
        status = "❌"
    results.append({
        "id": i+1,
        "question": item['q'],
        "answer": answer[:100],
        "keywords": item['keywords'],
        "status": status
    })
    print(f"{status} Q{i+1}: {item['q']}")
    print(f"   答: {answer[:80]}...")
    print(f"   关键词: {item['keywords']}")

accuracy = correct / len(test_questions) * 100
print(f"\n{'='*50}")
print(f"📊 准确率: {correct}/{len(test_questions)} = {accuracy:.1f}%")
print(f"{'='*50}")

# 保存结果
with open('accuracy_report.json', 'w', encoding='utf-8') as f:
    json.dump({"accuracy": accuracy, "total": len(test_questions), "correct": correct, "details": results}, f, ensure_ascii=False, indent=2)
print("📄 报告已保存: accuracy_report.json")
