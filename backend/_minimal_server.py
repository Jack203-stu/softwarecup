from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

PRESET_REPLIES = {
    '你是谁': '我是小灵，灵山胜境的AI数字导游。',
}

def get_preset_reply(text):
    for key, reply in PRESET_REPLIES.items():
        if key in text:
            return reply
    if '梵宫' in text and ('火灾' in text or '烧' in text):
        return 'FANU_REPLY_2016_2017_REBUILD'
    if '灵山精舍' in text:
        return 'JINGSHE_ZHUXIE_CHANSU'
    return None

@app.post('/api/chat/text')
async def chat(req: dict):
    text = req.get('text', '')
    preset = get_preset_reply(text)
    if preset:
        return {'question': text, 'answer': preset, 'sources': ['(内置)']}
    return {'question': text, 'answer': f'RAG_ANSWER_FOR_{text[:20]}', 'sources': ['KB']}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
