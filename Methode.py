import os
import re
import warnings

import pdfplumber
import stanza

stanza.download('de')
nlp = stanza.Pipeline('de', processors='tokenize,mwt,pos,lemma')

from transformers import MarianMTModel, MarianTokenizer

model_name = "Helsinki-NLP/opus-mt-de-zh"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)


def translate_to_chi(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)

    outputs = model.generate(
        **inputs,
        max_length=100,
        num_beams=4,
        no_repeat_ngram_size=2,
        early_stopping=True,
        length_penalty=1.5,
        temperature=0.7,  # 降低输出的随机性
        top_k=50,  # 限制候选词数量
        top_p=0.95,  # 核采样阈值
    )

    # 后处理
    translated = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # 移除可能的重复和None
    translated = "".join(dict.fromkeys(translated.split())) if translated else ""
    return translated


class MdFormat:
    def __init__(self, count, deu, chi, gen):
        self.count = count
        self.deu = deu
        self.chi = chi
        self.gen = gen

    def __FORM__(self):
        if self.gen is not None:
            return f"{self.count} {self.gen} {self.deu} {self.chi}"
        else:
            return f"{self.count} {self.deu} {self.chi}"


def extract_words_from_pdf(pdf_path):
    import logging
    logging.getLogger('pdfminer').setLevel(logging.ERROR)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=UserWarning)
        words = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                cleaned_text = text.replace('\n', ' ')
                words += cleaned_text
    return words


def process_words(words, german_characters):
    word_count_dict = {}
    for word in words:
        word = word.strip()
        if word == "":
            continue
        if not re.match(f"^[{german_characters}]+$", word):
            continue
        if word in word_count_dict:
            word_count_dict[word] += 1
        else:
            word_count_dict[word] = 1
    return word_count_dict


def extract_word_dict_from_docx(file_path):
    """
    读取一个markdown文件，记录其中由德语字母组成的单词，并统计每个单词的出现次数。

    :param file_path: markdown文件或pdf的路径
    :return: 记录单词出现次数的字典
    """
    german_characters = "äöüßÄÖÜẞabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

    if file_path.endswith(".md"):
        with open(file_path, 'r', encoding='utf-8') as file:
            words = file.read().split(" ")
    elif file_path.endswith(".pdf"):
        line = extract_words_from_pdf(file_path)
        words = line.split(" ")
    else:
        return {}

    return process_words(words, german_characters)


class Constants:
    New_ = 'Neue_Wörter.md'
    Old_ = 'Alte_Wörter.md'
    type1 = ' ' * 5
    type2 = ' ' * 10
    type3 = ' ' * 15


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
        subdir = [d for d in os.listdir(abs_path) if os.path.isdir(os.path.join(abs_path, d))]
        sorted_subdir = sorted(subdir)
        return [os.path.join(abs_path, subdir) for subdir in sorted_subdir]
    except FileNotFoundError:
        print(f"错误：{abs_path} 目录不存在")
        return []


def count_dict_add(dict0, lemma, value=1):
    if lemma in dict0:
        dict0[lemma] += value
    else:
        dict0[lemma] = value


def count_dict_add_dict(dict0, dict1):
    for key, value in dict1.items():
        if key in dict0:
            dict0[key] += value
        else:
            dict0[key] = value


def get_noun_gender(word: str):
    """
    获取德语名词的性别（Der/Die/Das）
    :param word: 德语名词
    :return: 性别标识字符串或None（非名词时）
    """
    global nlp
    if nlp is None:
        raise RuntimeError("请先安装德语模型，运行命令: stanza.download('de')")

    doc = nlp(word)

    for sent in doc.sentences:
        for token in sent.tokens:
            # 处理多词token
            for word_info in token.words:
                if word_info.upos != 'NOUN':
                    continue

                # 解析形态特征
                feats = {f.split('=')[0]: f.split('=')[1]
                         for f in (word_info.feats or '').split('|')
                         if '=' in f}

                # 处理复数形式
                if feats.get('Number') == 'Plur':
                    return 'Die'

                # 解析单数性别
                gender = feats.get('Gender')
                if gender in ['Masc', 'Fem', 'Neut']:
                    return {'Masc': 'Der', 'Fem': 'Die', 'Neut': 'Das'}[gender]

    return None


def classify(deu):
    global nlp
    if nlp is None:
        raise RuntimeError("请先安装德语模型，运行命令: stanza.download('de')")
    doc = nlp(deu.lower())
    for sent in doc.sentences:
        for token in sent.tokens:
            for word_info in token.words:
                return word_info


if __name__ == '__main__':
    print(get_noun_gender('Abgas'))
