import urllib.request, json, sys, time

time.sleep(6)

def api_call(q):
    data = json.dumps({'text': q, 'tags': []}).encode()
    req = urllib.request.Request(
        'http://localhost:8000/api/chat/text', data=data,
        method='POST', headers={'Content-Type':'application/json'}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())

for q in ['你好','梵宫发生过火灾吗？','灵山精舍是什么？','灵山大佛有多高？']:
    try:
        r = api_call(q)
        print(f'Q: {q}')
        print(f'A: {r.get("answer","")[:100]}')
        print(f'S: {r.get("sources",[])}')
        print()
    except Exception as e:
        print(f'Q: {q} ERR {e!r}')
        print()
