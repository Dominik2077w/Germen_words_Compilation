import json

import stanza

from Const import *
from myhttp import process_array, ask_deepseek

stanza.download('de', model_dir=str(Constants.CACHE_DIR))
nlp = stanza.Pipeline('de', model_dir=str(Constants.CACHE_DIR), processors='tokenize,lemma',
                      tokenize_no_ssplit=True)

import re


def convert_math_blocks_and_fix_erf(input_string):
    # 替换 \[ 和 \] 为 $$
    input_string = input_string.replace(r'\[', '$$')
    input_string = input_string.replace(r'\]', '$$')

    # 替换 \erf 为 \operatorname{erf}
    input_string = re.sub(r'\\erf', r'\\operatorname{erf}', input_string)

    # 将 $...$ 中的 \begin{array}...\end{array} 替换为纯内容（行内公式兼容）
    pattern = re.compile(
        r'\$(.*?)\\begin{array}{[^}]*}(.*?)\\end{array}(.*?)\$',
        re.DOTALL
    )

    def array_replacer(match):
        before = match.group(1).strip()
        content = match.group(2).strip()
        after = match.group(3).strip()
        combined = ' '.join(filter(None, [before, content, after]))
        return f'${combined}$'

    prev = None
    while input_string != prev:
        prev = input_string
        input_string = pattern.sub(array_replacer, input_string)

    # 处理 $_{...}$ 结构，将其转化为 $ _{...} $
    input_string = re.sub(r'(\$_{[^}]*}\$)', r'$ \1 $', input_string)

    return input_string


import os
import subprocess


def convert_md_to_pdf(md_abs_path):
    """
    将 Markdown 文件渲染为同名 PDF 文件，保存在相同目录下，使用 markdown-pdf 工具。

    参数:
    - md_abs_path: Markdown 文件的绝对路径
    """
    if not os.path.isabs(md_abs_path):
        raise ValueError("请输入 Markdown 文件的绝对路径。")
    if not os.path.exists(md_abs_path):
        raise FileNotFoundError(f"文件不存在：{md_abs_path}")
    if not md_abs_path.lower().endswith(".md"):
        raise ValueError("输入文件必须是 .md 格式的 Markdown 文件。")

    # 生成输出 PDF 路径
    base_name = os.path.splitext(os.path.basename(md_abs_path))[0]
    output_pdf_path = os.path.join(os.path.dirname(md_abs_path), base_name + ".pdf")

    # markdown-pdf 命令
    command = [
        "markdown-pdf", md_abs_path
    ]

    try:
        subprocess.run(command, check=True)
        print(f"✅ 成功生成 PDF 文件：{output_pdf_path}")
    except subprocess.CalledProcessError as e:
        print("❌ 生成 PDF 时发生错误：", e)


class UsedDict:
    def __init__(self):
        self.used_dict = {}
        self.load_used_dict()

    def load_used_dict(self):
        try:
            with open(Constants.USED_DICT_PATH, 'r', encoding='utf-8') as f:
                self.used_dict = json.load(f)
        except FileNotFoundError:
            self.used_dict = {}
        except json.JSONDecodeError:
            self.used_dict = {}
            print(f"错误：缓存文件 {Constants.USED_DICT_PATH} 格式错误，已重置为默认值")

    def save_used_dict(self):
        with open(Constants.USED_DICT_PATH, 'w', encoding='utf-8') as f:
            json_code = json.dumps(self.used_dict, ensure_ascii=False, indent=4)
            f.write(json_code)

    def set_uesd_dict(self, key, value):
        self.used_dict[key] = value

    def get_uesd_dict(self, key):
        if key in self.used_dict:
            return self.used_dict[key]
        else:
            value = classify(key)
            self.set_uesd_dict(key, value)
            self.save_used_dict()
            return value


usedDict = UsedDict()


def teilen_words_250_in_str_list(classified_words_set):
    """
        将词集按每250个一组分割，并转换为字符串数组
        :param classified_words_set: 输入的词集
        :return: 字符串数组，每个字符串包含不超过250个空格分隔的单词
        """
    lst = sorted(classified_words_set)
    limit = 125
    result = []

    # 按每250个词分组
    for i in range(0, len(lst), limit):
        # 取出当前组的词并用空格连接
        group = lst[i:i + limit]
        result.append(" ".join(group))

    return result


def teilen_md_1200_in_string_list(text) -> list[str]:
    limit = 476
    ans = []
    while len(text) > limit:
        i = limit
        while text[i - 1] != '\n' and i > 0:
            i -= 1
        if i == 0:
            i = limit
            while text[i - 1] != '\n' and i < len(text):
                i += 1
            if i == len(text):
                ans.append(text)
                return ans
        ans.append(text[:i])
        text = text[i:]
    if len(text) > 0:
        ans.append(text)
    return ans


def deepseek_notizen_for_md_file(text) -> str:
    stringlist = teilen_md_1200_in_string_list(text)
    json_print(stringlist)
    md_pices = process_array(stringlist, notize_word)
    return "\n\n***************\n\n".join(md_pices)


def notize_word(word, status):
    return ask_deepseek(Constants.PromptForNotizen, word, status)


def format_word(word, status):
    return ask_deepseek(Constants.PromptForFormat, word, status)


def deepseek_format_to_words_md(classified_words_set):
    StringList = process_array(teilen_words_250_in_str_list(classified_words_set), format_word)
    ans = []
    for i in StringList:
        ans += i.split("\n")
    ans = [i for i in ans if i]
    ans = [i for i in ans if len(i) > 1]
    return sorted(ans)


def format_to_words_md(classified_words_set):
    limit = 250
    words = sorted(classified_words_set)
    while len(words) > limit:
        nowWord = "\n".join(words[:limit])


def classify_words(words) -> set:
    global usedDict
    new_words = set()
    for word in words:
        if word:
            new_words.add(usedDict.get_uesd_dict(word))
    return new_words


def classify(deu):
    """
    对单词进行词形还原
    """
    global nlp
    doc = nlp(deu)
    for sent in doc.sentences:
        for token in sent.tokens:
            for word_info in token.words:
                my_print2(f"{word_info.text} {word_info.lemma} {word_info.upos} {word_info.deprel}", 1)
                return word_info.lemma
            return None
        return None
    return None


def filter_german_words(words):
    # 定义德语允许的字符集
    german_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZäöüßÄÖÜ')

    def is_german_word(word):
        return all(char in german_chars for char in word)

    # 过滤数组
    return [word for word in words if is_german_word(word)]


def read_text_and_get_set(text) -> set:
    text = text.replace("\n", " ")
    words = text.split(" ")
    words = filter_german_words(words)
    word_set = set(words)
    return word_set


def my_print1(txt, enter=0):
    print(f'\r{" " * 100}', end="")
    if enter == 1:
        print(f"\r{Constants.type1}{txt}", flush=True)
    else:
        print(f"\r{Constants.type1}{txt}", end="", flush=True)


def my_print2(txt, enter=0):
    print(f'\r{" " * 100}', end="")
    if enter == 1:
        print(f"\r{Constants.type2}{txt}", flush=True)
    else:
        print(f"\r{Constants.type2}{txt}", end="", flush=True)


def my_print3(txt, enter=0):
    print(f'\r{" " * 100}', end="")
    if enter == 1:
        print(f"\r{Constants.type3}{txt}", flush=True)
    else:
        print(f"\r{Constants.type3}{txt}", end="", flush=True)


def get_sorted_abs_part_subdir(abs_path):
    try:
        # List directories, skipping hidden ones (those starting with '.')
        subdir = [d for d in os.listdir(abs_path)
                  if os.path.isdir(os.path.join(abs_path, d)) and not d.startswith('.')]

        sorted_subdir = sorted(subdir)
        return [os.path.join(abs_path, subdir) for subdir in sorted_subdir]

    except FileNotFoundError:
        print(f"错误：{abs_path} 目录不存在")
        return []


def json_print(json_obj):
    """
    打印json对象
    :param json_obj: json对象
    :return: None
    """
    print(json.dumps(json_obj, indent=4, ensure_ascii=False))
