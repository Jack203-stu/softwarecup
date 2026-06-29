import urllib.request, json

tests = [
    ('梵宫发生过火灾吗？',['火灾','2016','2017','重建']),
    ('灵山精舍是什么？',['精舍','禅修','住宿','酒店']),
    ('灵山佛学院成立于哪一年？',['2003','2004','佛学院']),
]
passed = 0
total = len(tests)
for q, expect in tests:
    data = json.dumps({'text': q, 'tags': []}).encode()
    req = urllib.request.Request('http://localhost:8000/api/chat/text', data=data,
                                method='POST', headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            r = json.loads(resp.read().decode())
        a = r.get('answer', '')
        hit = any(k in a for k in expect)
        if hit: passed += 1
        print(('OK ' if hit else 'FAIL'), q[:22], '=>', a[:70])
    except Exception as e:
        print('ERR', q[:22], '=>', repr(e)[:60])
print(f'准确率 = {passed}/{total} = {passed/total*100:.1f}%')
