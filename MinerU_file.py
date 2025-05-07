import json
import os

from Const import Constants
from tools import *


class MinerU:
    def __init__(self,full_path):
        self.full_path = full_path
        self.current_set = set()
        self.folder_appeared_set = set()

    def find_content_json(self):
        try:
            for root, dirs, files in os.walk(self.full_path):
                # 过滤掉隐藏目录
                dirs[:] = [d for d in dirs if not d.startswith('.')]

                # 查找以_content_list.json结尾的文件
                for file in files:
                    if file.endswith('_content_list.json'):
                        full_path = os.path.abspath(os.path.join(root, file))
                        my_print2(f"找到内容文件: {full_path}", 1)
                        return full_path

            my_print2(f"未找到 *_content_list.json 文件{self.full_path}", 1)
            return None

        except FileNotFoundError:
            my_print2(f"错误：目录 {self.full_path} 不存在", 1)
        except PermissionError:
            my_print2(f"错误：没有权限访问 {self.full_path}", 1)
    def __run__(self)-> set:
        if self.find_content_json():
            return ContentJson(self.find_content_json()).__run__()
        else:
            my_print2(f"未找到 *_content_list.json 文件{self.full_path}", 1)
            return set()


class ContentJson:
    def __init__(self, full_path):
        self.full_path = full_path

    def __run__(self)-> set:
        text=self.read()
        #notized_md=convert_math_blocks_and_fix_erf(deepseek_notizen_for_md_file(text))
        notized_md = deepseek_notizen_for_md_file(text)
        #同名保存到上上级目录的Results文件夹中
        os.makedirs(os.path.join(os.path.dirname(os.path.dirname(self.full_path)), Constants.Results_), exist_ok=True)
        filename_without_ext = os.path.splitext(os.path.basename(self.full_path))[0]
        md_file_full_path = os.path.join(os.path.dirname(os.path.dirname(self.full_path)), Constants.Results_, filename_without_ext + ".md")
        with open(md_file_full_path, 'w', encoding='utf-8') as f:
            f.write(notized_md)
        convert_md_to_pdf(md_file_full_path)
        return read_text_and_get_set(text)
    def read(self):
                try:
                    with open(self.full_path, 'r', encoding='utf-8') as f:
                        data = json.loads(f.read())
                        # 提取所有text类型项目的text值并拼接
                        text_contents = []
                        for item in data:
                            if item.get('type') in ['text','equation'] and 'text' in item :
                                if not item['text']:
                                    continue
                                text_contents.append(item['text'])
                        return '\n\n'.join(text_contents)
                except FileNotFoundError:
                    my_print2(f"错误：文件 {self.full_path} 不存在", 1)
                    return ""
                except json.JSONDecodeError:
                    my_print2(f"错误：read文件 {self.full_path} 不是有效的JSON格式", 1)
                    return ""
                except Exception as e:
                    my_print2(f"错误：read处理JSON文件时发生异常: {str(e)}", 1)
                    return ""