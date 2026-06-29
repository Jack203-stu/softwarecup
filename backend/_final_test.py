import urllib.request, json, time, sys

def ask(q, retries=2, delay=8):
    last_err = None
    for attempt in range(retries+1):
        try:
            data = json.dumps({'text': q, 'tags': []}).encode()
            req = urllib.request.Request(
                'http://localhost:8000/api/chat/text', data=data,
                method='POST', headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(delay)
    return {'answer': f'[ERR] {last_err!r}', 'sources': []}

TEST = [
    ('灵山大佛今天开放吗？开放时间是几点？',['开放时间','9','09','17','16','开园','营业']),
    ('灵山胜境的门票多少钱？',['门票','元','票价','180','210','成人']),
    ('请问灵山胜境几点开门几点关门？',['09','17','16','开园时间']),
    ('灵山大佛有多高？',['88','88米','八十八']),
    ('灵山大佛是什么材料造的？',['青铜','铜','锡青铜']),
    ('灵山大佛的手势是什么意思？',['施无畏','施与愿','无畏印','与愿印','右手举','左手下垂']),
    ('九龙灌浴是什么时候开始？',['10','14','16','十点','下午','一场']),
    ('九龙灌浴是灵山胜境的什么？',['仪式','表演','项目','喷泉','音乐']),
    ('九龙灌浴的喷泉有多少个龙头？',['九','9']),
    ('梵宫是什么时候建的？',['2008','2009','2010']),
    ('梵宫里面有什么？',['木雕','壁画','灯光','吊顶','文化','长廊']),
    ('梵宫发生过火灾吗？什么时候重建的？',['火灾','2016','2017','重建']),
    ('灵山胜境的建造缘起是什么？',['赵朴初','佛教','遗址','唐','祥符禅寺']),
    ('灵山胜境在无锡哪个区？',['滨湖区','马山']),
    ('灵山佛学院成立于哪一年？',['2003','2004','佛学院']),
    ('第一次去灵山胜境应该怎么游览？',['路线','建议','顺序','上午','下午','安排']),
    ('灵山胜境附近有什么吃饭的地方？',['餐饮','素斋','梵宫','灵山精舍']),
    ('灵山精舍是什么？',['精舍','禅修','住宿','酒店']),
]

print('='*60)
print(' 最终准确率测试（带重试）')
print(f'测试题数 = {len(TEST)}')
print('='*60)

passed = 0
total = len(TEST)

for i, (q, expect) in enumerate(TEST, 1):
    t0 = time.time()
    r = ask(q)
    dt = time.time() - t0
    a = r.get('answer', '')
    ok = any(k in a for k in expect) and not a.startswith('[ERR]')
    if ok: passed += 1
    status = '✅' if ok else '❌'
    detail = ('命中:'+ '+'.join([k for k in expect if k in a][:3])) if ok else ('重试失败' if a.startswith('[ERR]') else '关键词未命中')
    print(f'[{i:02d}/{total:02d}] {status} Q: {q[:25]}...  ({dt:.1f}s) {detail}')
    if not ok:
        print(f'     A: {a[:80]}')
        print(f'     S: {r.get("sources",[])}')

acc = passed/total*100
print()
print('='*60)
print(f' 准确率 = {passed}/{total} = {acc:.1f}%')
print('='*60)
