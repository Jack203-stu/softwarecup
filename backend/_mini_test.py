def get_preset_reply(text):
    PRESET_REPLIES = {'你好':'hi','嗨':'hey'}
    for key, reply in PRESET_REPLIES.items():
        if key in text:
            return reply
    if '梵宫' in text and ('火灾' in text or '烧' in text):
        return 'FANU_ZZ_CASE'
    if '灵山精舍' in text:
        return 'JINGSHE_ZZ_CASE'
    return None

if __name__ == '__main__':
    print('FANU:', get_preset_reply('梵宫发生过火灾吗？什么时候重建的？'))
    print('JINGSHE:', get_preset_reply('灵山精舍是什么？'))
    print('NIHAO:', get_preset_reply('你好'))
    print('X:', get_preset_reply('灵山大佛有多高？'))
