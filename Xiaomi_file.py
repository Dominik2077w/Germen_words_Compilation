import os
from pathlib import Path

from Const import Constants
from tools import read_text_and_get_set, deepseek_notizen_for_md_file, convert_md_to_pdf


class Xiaomi:
    def __init__(self, full_path):
        self.full_path = full_path

    def __run__(self) -> set:
        text = Path(self.full_path).read_text()
        notized_md = deepseek_notizen_for_md_file(text)
        # 同名保存到同目录的Results文件夹中
        os.makedirs(os.path.join(os.path.dirname(self.full_path), Constants.Results_), exist_ok=True)
        filename_without_ext = os.path.splitext(os.path.basename(self.full_path))[0]
        md_file_full_path=os.path.join(os.path.dirname(self.full_path), Constants.Results_, filename_without_ext + ".md")
        with open(md_file_full_path, 'w', encoding='utf-8') as f:
            f.write(notized_md)
        convert_md_to_pdf(md_file_full_path)
        return read_text_and_get_set(text)
