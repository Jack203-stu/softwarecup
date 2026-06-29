import urllib.request, json, sys

BASE = "http://localhost:8000"

def debug_call(q):
    print(f"\n{'='*60}")
    print(f"[REQUEST] {q}")

    # Try preset first
    from main import get_preset_reply
    preset = get_preset_reply(q)
    print(f"[PRESET_CHECK] result={preset is not None}", flush=True)

    # Full API call
    data = json.dumps({'text': q, 'tags': []}).encode()
    req = urllib.request.Request(
        f"{BASE}/api/chat/text", data=data,
        method='POST', headers={'Content-Type':'application/json'}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        r = json.loads(resp.read().decode())

    print(f"[ANSWER] {r.get('answer','')[:200]}")
    print(f"[SOURCES] {r.get('sources',[])}")

debug_call('梵宫发生过火灾吗？什么时候重建的？')
debug_call('灵山精舍是什么？')
debug_call('你好')
debug_call('灵山大佛有多高？')
