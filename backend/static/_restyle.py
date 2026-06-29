# -*- coding: utf-8 -*-
import re
from pathlib import Path

HERE = Path(r"d:\softwarecup\softwarecup\backend\static")

def read(p):
    return Path(p).read_text(encoding="utf-8")

def replace_style_block(html: str, new_style: str) -> str:
    return re.sub(r"(?is)<style>.*?</style>", new_style.strip(), html, count=1)

def apply(src, dst):
    raw = read(src)
    out = replace_style_block(raw, read(src))
    out2 = replace_style_block(raw, src.read_text(encoding="utf-8"))
    dst.write_text(out2, encoding="utf-8", newline="")

ADMIN_SRC = HERE / "_admin_light.txt"
AVATAR_SRC = HERE / "_avatar_light.txt"

for src, dst in [(ADMIN_SRC, HERE / "admin.html"), (AVATAR_SRC, HERE / "avatar-manage.html")]:
    new_style = read(src)
    raw = dst.read_text(encoding="utf-8")
    out = replace_style_block(raw, new_style)
    if out == raw:
        raise RuntimeError(f"could not find <style> in {dst.name}")
    dst.write_text(out, encoding="utf-8", newline="")
    print(f"re-styled {dst.name}: {len(raw)} -> {len(out)}")

print("OK")
