import subprocess, time, urllib.request, json, os, sys

subprocess.run(['taskkill','/F','/IM','python.exe'], shell=True, capture_output=True)
time.sleep(3)

print('Starting server...', flush=True)
p = subprocess.Popen([sys.executable, 'main.py'], cwd=r'd:\softwarecup\softwarecup\backend',
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
print(f'Server PID={p.pid}', flush=True)

time.sleep(8)

def ask(q):
    data = json.dumps({'text': q, 'tags': []}).encode()
    req = urllib.request.Request('http://localhost:8000/api/chat/text', data=data,
                                method='POST', headers={'Content-Type':'application/json'})
    r = json.loads(urllib.request.urlopen(req, timeout=60).read().decode())
    return r.get('answer','')

for q in ['梵宫发生过火灾吗？','灵山精舍是什么？','你好']:
    try:
        a = ask(q)
        print(f'Q: {q} => A: {a[:80]}', flush=True)
    except Exception as e:
        print(f'Q: {q} ERR {e}', flush=True)

p.terminate()
out = p.stdout.read().decode(errors='ignore')
print('\n=== SERVER STDOUT LAST 800 CHARS ===')
print(out[-800:])
