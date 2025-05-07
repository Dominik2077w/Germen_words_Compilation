import os

from Const import Constants
from folder import Folder
from tools import get_base_dir, usedDict


class Project:
    def __init__(self, path):
        if os.path.isabs(path):
            self.target_dir = path
        else:
            self.target_dir = os.path.join(Constants.BASE_DIR, path)

    def __run__(self):
        base_dir = self.target_dir
        print("全目录覆盖处理:", self.target_dir)
        try:
            for entry in os.listdir(base_dir):
                full_path = os.path.join(base_dir, entry)

                # Skip hidden directories
                if entry.startswith('.'):
                    continue

                if os.path.isdir(full_path):
                    rel_path = os.path.relpath(full_path, get_base_dir())
                    print(rel_path)
                    Folder(rel_path).__run__()
        except FileNotFoundError:
            os.makedirs(base_dir, exist_ok=True)
            print(f"目录 {base_dir} 已自动创建")