import subprocess, time, urllib.request, json, sys, os

print('=== Step 1: kill python ===')
subprocess.run(['taskkill','/F','/IM','python.exe'], capture_output=True)
time.sleep(2)

print('=== Step 2: start server ===')
os.chdir(r'd:\softwarecup\softwarecup\backend')
p = subprocess.Popen([sys.executable, 'main.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)

time.sleep(10)

print('=== Step 3: test requests ===')
for q in ['你好','梵宫发生过火灾吗？','灵山精舍是什么？']:
    try:
        data = json.dumps({'text': q, 'tags': []}).encode()
        req = urllib.request.Request('http://localhost:8000/api/chat/text', data=data, method='POST',
                                      headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=60) as resp:
            r = json.loads(resp.read().decode())
        print(f'Q: {q}')
        print(f'A: {r.get("answer","")[:120]}')
    except Exception as e:
        print(f'Q: {q} ERR {repr(e)[:100]}')

print('=== Step 4: capture server output ===')
p.terminate()
try:
    out = p.stdout.read().decode(errors='ignore')
    print(out[-1500:])
except: pass
