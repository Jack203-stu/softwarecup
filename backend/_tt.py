import urllib.request, json, sys
for q in ['梵宫发生过火灾吗？什么时候重建的？','灵山精舍是什么？','你好']:
 p=json.dumps({'text':q,'tags':[]}).encode()
 req=urllib.request.Request('http://localhost:8000/api/chat/text',data=p,method='POST',headers={'Content-Type':'application/json'})
 try:
  r=json.loads(urllib.request.urlopen(req,timeout=60).read().decode())
  print('Q:',q,'=>',r.get('answer','')[:80])
 except Exception as e:
  print('ERR',q,e)
