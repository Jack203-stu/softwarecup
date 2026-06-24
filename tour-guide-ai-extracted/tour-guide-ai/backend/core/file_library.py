import os
import uuid
from typing import List, Dict

BASE_DIR = r"C:\Users\van\Desktop\aaa\t2\tour-guide-ai\backend"
LIBRARY_DIR = os.path.join(BASE_DIR, "..", "data", "library")

os.makedirs(LIBRARY_DIR, exist_ok=True)

class FileLibrary:
    def __init__(self):
        self.library_dir = LIBRARY_DIR

    def list_files(self) -> List[Dict]:
        """列出所有上传的文件"""
        files = []
        for fname in os.listdir(self.library_dir):
            if os.path.isfile(os.path.join(self.library_dir, fname)):
                files.append({
                    "id": fname,
                    "name": fname,
                    "path": os.path.join(self.library_dir, fname)
                })
        return files

    def upload_file(self, filename: str, content: bytes) -> str:
        """上传文件到库"""
        ext = os.path.splitext(filename)[1]
        new_name = f"{uuid.uuid4()}{ext}"
        save_path = os.path.join(self.library_dir, new_name)
        with open(save_path, "wb") as f:
            f.write(content)
        return new_name

    def delete_file(self, file_id: str) -> bool:
        """删除库中文件"""
        file_path = os.path.join(self.library_dir, file_id)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False

    def get_file_path(self, file_id: str) -> str:
        """获取文件路径"""
        return os.path.join(self.library_dir, file_id)