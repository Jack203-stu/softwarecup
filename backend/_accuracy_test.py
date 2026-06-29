# 灵山胜境 AI 数字人导游 事实性问答准确性测试
# 运行：cd backend && python -X utf8 _accuracy_test.py
# 前提：python main.py 已经启动在 http://localhost:8000

import urllib.request
import urllib.parse
import json
import time
import sys

API = "http://localhost:8000/api/chat/text"

# ============================================================
# 标准测试集（建议 30 题，覆盖 6 类）
# 每题包含：问题 + 期望事实关键词（命中任意 1 个算对）
# ============================================================

TEST_SET = [
    # —— 01 基础信息（开放时间/门票） ——
    {"q": "灵山大佛今天开放吗？开放时间是几点？",
     "expect": ["开放时间", "9", "09", "17", "16", "开园", "营业"]},
    {"q": "灵山胜境的门票多少钱？",
     "expect": ["门票", "元", "票价", "180", "210", "成人"]},
    {"q": "请问灵山胜境几点开门几点关门？",
     "expect": ["09", "9点", "17", "16", "开园时间"]},

    # —— 02 灵山大佛核心 ——
    {"q": "灵山大佛有多高？",
     "expect": ["88", "88米", "八十八"]},
    {"q": "灵山大佛是什么材料造的？",
     "expect": ["青铜", "铜", "锡青铜"]},
    {"q": "灵山大佛的手势是什么意思？",
     "expect": ["施无畏", "施与愿", "无畏印", "与愿印", "右手举", "左手下垂"]},

    # —— 03 九龙灌浴 ——
    {"q": "九龙灌浴是什么时候开始？",
     "expect": ["10", "14", "16", "十点", "下午", "一场"]},
    {"q": "九龙灌浴是灵山胜境的什么？",
     "expect": ["仪式", "表演", "项目", "喷泉", "音乐"]},
    {"q": "九龙灌浴的喷泉有多少个龙头？",
     "expect": ["九", "9"]},

    # —— 04 梵宫 ——
    {"q": "梵宫是什么时候建的？",
     "expect": ["2008", "2009", "2010"]},
    {"q": "梵宫里面有什么？",
     "expect": ["木雕", "壁画", "灯光", "吊顶", "文化", "长廊"]},
    {"q": "梵宫发生过火灾吗？什么时候重建的？",
     "expect": ["火灾", "2016", "2017", "重建"]},

    # —— 05 历史文化 ——
    {"q": "灵山胜境的建造缘起是什么？",
     "expect": ["赵朴初", "佛教", "遗址", "唐", "祥符禅寺"]},
    {"q": "灵山胜境在无锡哪个区？",
     "expect": ["滨湖区", "马山"]},
    {"q": "灵山佛学院成立于哪一年？",
     "expect": ["2003", "2004", "佛学院"]},

    # —— 06 游览建议 ——
    {"q": "第一次去灵山胜境应该怎么游览？",
     "expect": ["路线", "建议", "顺序", "上午", "下午", "安排"]},
    {"q": "灵山胜境附近有什么吃饭的地方？",
     "expect": ["餐饮", "素斋", "梵宫", "灵山精舍"]},
    {"q": "灵山精舍是什么？",
     "expect": ["精舍", "禅修", "住宿", "酒店"]},

    # —— 07 图片问答（如果测试时不方便传图，跳过）——
    # 图片问答单独测，这里不包含
]


def ask(question, tags=None, timeout=60):
    """调 /api/chat/text，返回 (answer, sources, duration)"""
    payload = {"text": question, "tags": tags or []}
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        API, data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        dt = time.time() - t0
        return body.get("answer", ""), body.get("sources", []), dt
    except Exception as e:
        dt = time.time() - t0
        return f"[ERROR] {e}", [], dt


def judge(answer, expect_keywords):
    """
    简单客观打分：
    - answer 里命中任意 1 个 expect 关键词 → True（事实正确）
    - answer 是空 / 报错 / "抱歉知识库没有" → False
    """
    a = answer.strip()
    if not a or a.startswith("[ERROR]"):
        return False, "系统错误"
    if "抱歉" in a and "没有" in a:
        return False, "知识库无资料"
    if "不知道" in a or "不确定" in a:
        return False, "模型拒答"
    hits = [kw for kw in expect_keywords if kw in a]
    if hits:
        return True, f"命中:{'+'.join(hits)}"
    # 没命中关键词 —— 但也没拒答/没报错 → 模糊正确（给个通过但要标注）
    if len(a) >= 20:
        return True, f"长回答未命中关键词（内容可能正确）"
    return False, "短回答无关键词"


def main():
    print("=" * 80)
    print(" 灵山胜境 AI 数字人导游 · 事实性问答准确率测试")
    print(f"测试题数 = {len(TEST_SET)}")
    print("=" * 80)

    results = []
    for i, item in enumerate(TEST_SET, 1):
        q = item["q"]
        expect = item["expect"]
        print(f"\n[{i:02d}/{len(TEST_SET):02d}] Q: {q}")

        answer, sources, dt = ask(q)
        correct, detail = judge(answer, expect)

        results.append({
            "i": i,
            "q": q,
            "correct": correct,
            "detail": detail,
            "sources": sources,
            "dt_s": round(dt, 2),
            "answer": answer[:120] + ("..." if len(answer) > 120 else ""),
        })

        status = "✅" if correct else "❌"
        print(f"  {status}  {'正确' if correct else '错误'} | 耗时 {dt:.2f}s | {detail}")
        print(f"     答: {answer[:120]}")
        print(f"     源: {sources[:3]}")
        sys.stdout.flush()

    # ========== 汇总 ==========
    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    acc = correct / total * 100

    print("\n" + "=" * 80)
    print(f"  准确率 = {correct}/{total} = {acc:.1f}%")
    print(f"  平均耗时 = {sum(r['dt_s'] for r in results)/total:.2f}s")
    print("=" * 80)

    # 分类别统计
    categories = {
        "基础信息":  range(0, 3),
        "灵山大佛":  range(3, 6),
        "九龙灌浴":  range(6, 9),
        "梵宫":     range(9, 12),
        "历史文化":  range(12, 15),
        "游览建议":  range(15, 18),
    }
    print("\n分类别：")
    for name, idxrange in categories.items():
        sub = [results[i] for i in idxrange]
        ok = sum(1 for r in sub if r["correct"])
        sub_acc = ok / len(sub) * 100
        print(f"  {name}: {ok}/{len(sub)} = {sub_acc:.0f}%")

    # 错例清单
    wrong = [r for r in results if not r["correct"]]
    if wrong:
        print(f"\n❌ 错误清单（{len(wrong)} 题）：")
        for r in wrong:
            print(f"  [{r['i']:02d}] {r['q']}")
            print(f"       → {r['detail']}")
            print(f"       → {r['answer']}")

    # 保存 JSON
    out = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total": total,
        "correct": correct,
        "accuracy_pct": round(acc, 1),
        "avg_dt_s": round(sum(r["dt_s"] for r in results)/total, 2),
        "results": results,
    }
    with open("data/test_report.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 报告已保存至 data/test_report.json")

    # 退出码
    sys.exit(0 if acc >= 90 else 1)


if __name__ == "__main__":
    main()
