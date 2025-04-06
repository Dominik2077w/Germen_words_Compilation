import re

import pdfplumber  # 替代 PyPDF2

import warnings



def extract_words_from_pdf(pdf_path):
    # 使用 warnings.catch_warnings() 上下文管理器
    import logging
    logging.getLogger('pdfminer').setLevel(logging.ERROR)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=UserWarning)
        words = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                # 改进的文本清理
                cleaned_text = text.replace('\n', ' ')
                words += cleaned_text
    return words

def extract_unique_german_words(file_path):
    """
    读取一个markdown文件，记录其中由德语字母组成的单词，并去重得到一个不重复的德语单词列表。
    
    :param file_path: markdown文件or pdf的路径
    :return: 不重复的德语单词列表
    """
    german_words = set()
    german_characters = (
    "äöüßÄÖÜẞabcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
)

    if file_path.endswith(".md"):
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                words = line.split(" ")
                for word in words:
                    word = word.strip()
                    if word == "":
                        continue
                    if not re.match(f"^[{german_characters}]+$", word):
                        continue
                    german_words.add(word)
    elif file_path.endswith(".pdf"):
        line = extract_words_from_pdf(file_path)
        words = line.split(" ")
        for word in words:
            word = word.strip()
            if word == "":
                continue
            if not re.match(f"^[{german_characters}]+$", word):
                continue
            german_words.add(word)

    return german_words


import os



def from_md_to_germen_set(relative_path):
    """
    处理指定目录下的所有.md文件，汇总德语单词
    
    :param relative_path: 相对于项目根目录的路径
    :return: 合并后的德语单词集合
    """
    german_words = set()
    abs_path = os.path.join(os.getcwd(), relative_path)

    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"目录不存在: {abs_path}")
    if not os.path.isdir(abs_path):
        raise NotADirectoryError(f"路径不是目录: {abs_path}")

    for root, dirs, files in os.walk(abs_path):
        for file in files:
            if (file.lower().endswith('.md') and not file.startswith("Neue_Wörter") and not file.startswith(
                    "Alte_Wörter")) or file.lower().endswith('.pdf'):
                file_path = os.path.join(root, file)
                try:
                    german_words.update(extract_unique_german_words(file_path))

                except Exception:
                    pass

    return german_words


def get_set_difference(a: set, b: set) -> set:
    """
    计算两个集合的差集（b - a）
    :param a: 第一个集合
    :param b: 第二个集合
    :return: 包含b中不在a中的元素的集合
    """
    return b - a
