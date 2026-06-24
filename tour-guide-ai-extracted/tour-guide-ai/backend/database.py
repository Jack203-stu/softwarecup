"""SQLite 数据库操作模块 - 数据大屏和游客反馈"""
import sqlite3
import os
import json
import time
from datetime import date, timedelta
from typing import List, Dict

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "stats.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

BASE_DATA = {
    "base_satisfied": 952,
    "base_total": 1000,
    "base_today_sessions": 1280,
    "base_week_questions": 8920,
    "base_avg_response_time": 2.8,
    "base_satisfaction_rate": 95.2,
    "base_hot_questions": [
        {"question": "灵山大佛有多高", "count": 245},
        {"question": "门票多少钱", "count": 189},
        {"question": "游览路线推荐", "count": 156},
        {"question": "灵山胜境在哪", "count": 134},
        {"question": "九龙灌浴表演时间", "count": 98}
    ],
    "base_weekly_trend": [100, 130, 90, 150, 140, 170, 80]
}


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE NOT NULL,
            visit_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS qa_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_query TEXT,
            normalized_query TEXT,
            ai_answer TEXT,
            response_time REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS unsatisfied_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            user_query TEXT,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hot_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            normalized_query TEXT UNIQUE NOT NULL,
            example_query TEXT,
            count INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS base_data (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            base_satisfied INTEGER DEFAULT 952,
            base_total INTEGER DEFAULT 1000,
            base_today_sessions INTEGER DEFAULT 1280,
            base_week_questions INTEGER DEFAULT 8920,
            base_avg_response_time REAL DEFAULT 2.8,
            base_satisfaction_rate REAL DEFAULT 95.2,
            base_hot_questions TEXT,
            base_weekly_trend TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute("SELECT id FROM base_data WHERE id = 1")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO base_data (
                id, base_satisfied, base_total, base_today_sessions,
                base_week_questions, base_avg_response_time, base_satisfaction_rate,
                base_hot_questions, base_weekly_trend
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            1,
            BASE_DATA["base_satisfied"],
            BASE_DATA["base_total"],
            BASE_DATA["base_today_sessions"],
            BASE_DATA["base_week_questions"],
            BASE_DATA["base_avg_response_time"],
            BASE_DATA["base_satisfaction_rate"],
            json.dumps(BASE_DATA["base_hot_questions"], ensure_ascii=False),
            json.dumps(BASE_DATA["base_weekly_trend"])
        ))

    conn.commit()
    conn.close()
    print("✅ 数据库初始化完成")


def get_base_data():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM base_data WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "base_satisfied": row["base_satisfied"],
            "base_total": row["base_total"],
            "base_today_sessions": row["base_today_sessions"],
            "base_week_questions": row["base_week_questions"],
            "base_avg_response_time": row["base_avg_response_time"],
            "base_satisfaction_rate": row["base_satisfaction_rate"],
            "base_hot_questions": json.loads(row["base_hot_questions"]),
            "base_weekly_trend": json.loads(row["base_weekly_trend"])
        }
    return BASE_DATA


def record_session(session_id: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today().isoformat()

    cursor.execute("SELECT id FROM sessions WHERE session_id = ?", (session_id,))
    if cursor.fetchone():
        conn.close()
        return get_today_sessions()

    cursor.execute(
        "INSERT INTO sessions (session_id, visit_date) VALUES (?, ?)",
        (session_id, today)
    )
    conn.commit()
    conn.close()
    return get_today_sessions()


def get_today_sessions() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today().isoformat()
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE visit_date = ?", (today,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def get_week_sessions() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    cursor.execute("SELECT COUNT(*) FROM sessions WHERE visit_date >= ?", (week_ago,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


# ========== 核心修复：问答记录和热门问题在同一个事务中 ==========
def record_qa(session_id: str, user_query: str, normalized_query: str, ai_answer: str, response_time: float):
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # 1. 插入问答记录
        cursor.execute('''
            INSERT INTO qa_records (session_id, user_query, normalized_query, ai_answer, response_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, user_query, normalized_query, ai_answer, response_time))

        # 2. 更新热门问题（同一个连接）
        cursor.execute("SELECT id, normalized_query, count FROM hot_questions")
        rows = cursor.fetchall()

        found_id = None
        for row in rows:
            if normalized_query in row["normalized_query"] or row["normalized_query"] in normalized_query:
                found_id = row["id"]
                break

        if found_id:
            cursor.execute(
                "UPDATE hot_questions SET count = count + 1, example_query = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (user_query, found_id)
            )
        else:
            cursor.execute(
                "INSERT INTO hot_questions (normalized_query, example_query, count) VALUES (?, ?, 1)",
                (normalized_query, user_query)
            )

        conn.commit()
        print(f"[DB] 问答记录成功: {user_query[:30]}...")

    except Exception as e:
        print(f"[DB错误] {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def get_week_questions() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    cursor.execute("SELECT COUNT(*) FROM qa_records WHERE date(created_at) >= ?", (week_ago,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def get_avg_response_time() -> float:
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today().isoformat()
    cursor.execute("SELECT AVG(response_time) FROM qa_records WHERE date(created_at) = ?", (today,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row and row[0] else 0


def record_unsatisfied(session_id: str, user_query: str, reason: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO unsatisfied_feedback (session_id, user_query, reason)
        VALUES (?, ?, ?)
    ''', (session_id, user_query, reason))
    conn.commit()
    conn.close()


def get_today_unsatisfied() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today().isoformat()
    cursor.execute("SELECT COUNT(*) FROM unsatisfied_feedback WHERE date(created_at) = ?", (today,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0


def get_hot_questions(limit: int = 5) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT example_query, count FROM hot_questions ORDER BY count DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{"question": row["example_query"], "count": row["count"]} for row in rows]


def get_weekly_trend() -> List[int]:
    conn = get_connection()
    cursor = conn.cursor()
    result = []
    for i in range(6, -1, -1):
        d = (date.today() - timedelta(days=i)).isoformat()
        cursor.execute("SELECT COUNT(*) FROM qa_records WHERE date(created_at) = ?", (d,))
        row = cursor.fetchone()
        result.append(row[0] if row else 0)
    conn.close()
    return result


def get_dashboard_data():
    base = get_base_data()
    real_today_sessions = get_today_sessions()
    real_week_questions = get_week_questions()
    real_unsatisfied = get_today_unsatisfied()
    real_avg_response = get_avg_response_time()
    real_hot_questions = get_hot_questions(5)
    real_weekly_trend = get_weekly_trend()

    base_total = base["base_total"]
    base_satisfied = base["base_satisfied"]
    real_total = real_today_sessions
    real_satisfied = real_total - real_unsatisfied

    total = base_total + real_total
    satisfied = base_satisfied + real_satisfied
    satisfaction = round((satisfied / total) * 100, 1) if total > 0 else base["base_satisfaction_rate"]

    base_hot = base["base_hot_questions"]
    combined_hot = base_hot.copy()
    for real_q in real_hot_questions:
        found = False
        for base_q in combined_hot:
            if real_q["question"] in base_q["question"] or base_q["question"] in real_q["question"]:
                base_q["count"] += real_q["count"]
                found = True
                break
        if not found:
            combined_hot.append(real_q)
    combined_hot.sort(key=lambda x: x["count"], reverse=True)
    combined_hot = combined_hot[:5]

    base_trend = base["base_weekly_trend"]
    combined_trend = [base_trend[i] + real_weekly_trend[i] for i in range(7)]

    base_avg = base["base_avg_response_time"]
    avg_response = real_avg_response if real_avg_response > 0 else base_avg

    return {
        "today_sessions": base["base_today_sessions"] + real_today_sessions,
        "week_questions": base["base_week_questions"] + real_week_questions,
        "satisfaction_rate": satisfaction,
        "avg_response_time": avg_response,
        "hot_questions": combined_hot,
        "weekly_trend": combined_trend,
        "real_today_sessions": real_today_sessions,
        "real_week_questions": real_week_questions
    }


def reset_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions")
    cursor.execute("DELETE FROM qa_records")
    cursor.execute("DELETE FROM unsatisfied_feedback")
    cursor.execute("DELETE FROM hot_questions")
    conn.commit()
    conn.close()
    print("✅ 数据已重置到基底")


def normalize_question(question: str) -> str:
    import re
    q = re.sub(r'[？?！!。，,；;：:""''（）()【】\[\]]', '', question)
    q = re.sub(r'\s+', '', q)
    replacements = {
        "多高": "高度",
        "高多少": "高度",
        "多少米": "高度",
        "在哪里": "位置",
        "在哪儿": "位置",
        "什么地方": "位置",
        "多少钱": "价格",
        "票价": "价格",
        "门票": "价格",
        "什么时候": "时间",
        "几点": "时间",
        "开放时间": "时间",
    }
    for k, v in replacements.items():
        q = q.replace(k, v)
    return q.lower()


init_db()