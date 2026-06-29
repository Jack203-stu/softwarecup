import sys
sys.path.insert(0, '.')
from main import get_preset_reply

r1 = get_preset_reply('梵宫发生过火灾吗？什么时候重建的？')
r2 = get_preset_reply('灵山精舍是什么？')
r3 = get_preset_reply('灵山大佛有多高？')
r4 = get_preset_reply('你好')

print('r1 is None:', r1 is None)
if r1:
    print('  r1[:60]:', r1[:60])
else:
    print('  r1 = None')

print('r2 is None:', r2 is None)
if r2:
    print('  r2[:60]:', r2[:60])

print('r3 is None:', r3 is None)
print('r4 is None:', r4 is None)
if r4:
    print('  r4[:60]:', r4[:60])
