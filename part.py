import os

from Const import Constants
from MinerU_file import MinerU
from Xiaomi_file import Xiaomi
from tools import my_print2, classify_words, deepseek_format_to_words_md


class Part:
    def __init__(self, abs_path: str, folder_appeared_set):
        self.abs_path = abs_path
        self.current_set = set()
        self.folder_appeared_set = folder_appeared_set

    def __run__(self, cutoff_date='        ALL'):
        try:
            # 获取目录下所有项目
            entries = os.listdir(self.abs_path)

            # 过滤隐藏文件
            visible_entries = [e for e in entries if (not e.startswith('.')) and (not e.startswith(Constants.Results_))]

            for entry in sorted(visible_entries):
                full_path = os.path.join(self.abs_path, entry)

                if os.path.isfile(full_path):
                    self.current_set.update(Xiaomi(full_path).__run__())

                elif os.path.isdir(full_path):
                    self.current_set.update(MinerU(full_path).__run__())


        except FileNotFoundError:
            my_print2(f"Part错误：目录 {self.abs_path} 不存在", 1)
        except PermissionError:
            my_print2(f"错误：没有权限访问 {self.abs_path}", 1)
        self.save_words_to_md(self.current_set - self.folder_appeared_set)
        self.folder_appeared_set.update(self.current_set)

    def save_words_to_md(self, words: set):
        classified_words_set = classify_words(words)
        md_lines_list = deepseek_format_to_words_md(classified_words_set)
        md_text = "\n".join(sorted(md_lines_list))
        self.save_md(md_text, Constants.New_)

    def save_md(self, md_text, param):
        try:
            os.makedirs(os.path.join(self.abs_path, Constants.Results_), exist_ok=True)
            with open(os.path.join(self.abs_path, Constants.Results_, param), 'w', encoding='utf-8') as f:
                f.write(md_text)
        except FileNotFoundError:
            my_print2(f"错误：目录 {self.abs_path} 不存在", 1)
