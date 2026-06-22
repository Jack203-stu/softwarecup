import os, zipfile
import docx

p = os.path.join('..','data','raw','灵山讲解词.docx')

ct = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
</Types>'''

rels_root = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

rels_doc = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''

styles = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
    <w:qFormat/>
  </w:style>
</w:styles>'''

body_text = '''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
  <w:p><w:r><w:t>灵山大佛：高88米，重700吨，位于无锡灵山胜境，1997年开光。</w></w:r></w:p>
  <w:p><w:r><w:t>梵宫：灵山胜境核心建筑，建筑面积7万平米，内有世界最大室内铜制释迦摩尼。</w></w:r></w:p>
  <w:p><w:r><w:t>门票价格：成人票210元每人，1.4米以下儿童免费，60岁以上半价。</w></w:r></w:p>
</w:body>
</w:document>'''

with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('[Content_Types].xml', ct.encode('utf-8'))
    z.writestr('_rels/.rels', rels_root.encode('utf-8'))
    z.writestr('word/_rels/document.xml.rels', rels_doc.encode('utf-8'))
    z.writestr('word/styles.xml', styles.encode('utf-8'))
    z.writestr('word/document.xml', body_text.encode('utf-8'))

print('docx written to', p)
d = docx.Document(p)
print('docx paragraphs:', [x.text for x in d.paragraphs])
