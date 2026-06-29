import sys; sys.path.insert(0, '.')
from main import get_preset_reply, PRESET_REPLIES
print('FANU:', repr(get_preset_reply('梵宫发生过火灾吗？什么时候重建的？')))
print('JINGSHE:', repr(get_preset_reply('灵山精舍是什么？')))
print('NIHAO:', repr(get_preset_reply('你好')))
print('PRESET_KEYS:', list(PRESET_REPLIES.keys()))
print('test contains "梵宫":', '梵宫' in '梵宫发生过火灾吗？')
print('test contains "火灾":', '火灾' in '梵宫发生过火灾吗？')
