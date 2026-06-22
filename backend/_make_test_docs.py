import os, zipfile, xml.etree.ElementTree as ET
import openpyxl

os.makedirs(os.path.join('..','data','raw'), exist_ok=True)

# 1) docx
p = os.path.join('..','data','raw','灵山讲解词.docx')
with zipfile.ZipFile(p,'w') as z:
    xml = '<?xml version="1.0"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>' \
          '<w:p><w:r><w:t>灵山大佛：高88米，重700吨，位于无锡灵山胜境，1997年开光。</w></w:r></w:p>' \
          '<w:p><w:r><w:t>梵宫：灵山胜境核心建筑，建筑面积7万平米，内有世界最大室内铜制释迦摩尼。</w></w:r></w:p>' \
          '<w:p><w:r><w:t>门票价格：成人票210元/人；1.4米以下儿童免费；60岁以上半价。</w></w:r></w:p>' \
          '</w:body></w:document>'
    z.writestr('word/document.xml', xml.encode('utf-8'))
    z.writestr('[Content_Types].xml', '<Types/>')
    z.writestr('_rels/.rels', '<Relationships/>')
print('docx ok', p)

# 2) xlsx
p2 = os.path.join('..','data','raw','常见问答.xlsx')
wb = openpyxl.Workbook()
ws = wb.active; ws.title='常见问答'
ws.append(['问题','回答'])
ws.append(['灵山胜境在哪里','江苏省无锡市滨湖区马山街道'])
ws.append(['开放时间','全年 07:30 - 17:30'])
ws.append(['推荐游览路线','照壁→佛手广场→梵宫→五印坛城→灵山小镇'])
wb.save(p2)
print('xlsx ok', p2)

# 3) txt
p3 = os.path.join('..','data','raw','文史资料.txt')
with open(p3,'w',encoding='utf-8') as f:
    f.write('灵山胜境景区始建于1994年，1997年建成灵山大佛。\n'
            '景区以佛教文化为主题，占地约1200亩。\n'
            '梵宫大厅穹顶直径26米，象征佛教圆满。')
print('txt ok', p3)
