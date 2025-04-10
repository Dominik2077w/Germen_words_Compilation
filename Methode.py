import os
import re
import warnings

import pdfplumber
import stanza

stanza.download('de', package='de_hdt_large')
nlp = stanza.Pipeline('de', processors='tokenize,mwt,pos,lemma')

import requests
import random
import hashlib
import json

# 全局变量 - 替换为你自己的百度翻译API凭证
APP_ID = ''
SECRET_KEY = ''


def translate_to_chi_baidu(text):
    """
    使用百度翻译API将德语文本翻译成中文

    参数:
        text (str): 要翻译的德语文本

    返回:
        str: 翻译后的中文文本
        str: 如果翻译失败返回空字符串(与原函数行为一致)
    """
    # 百度翻译API的URL
    url = 'https://fanyi-api.baidu.com/api/trans/vip/translate'

    # 源语言为德语(de)，目标语言为中文(zh)
    from_lang = 'de'
    to_lang = 'zh'

    # 生成随机数
    salt = random.randint(32768, 65536)

    # 计算签名
    sign_str = APP_ID + text + str(salt) + SECRET_KEY
    sign = hashlib.md5(sign_str.encode()).hexdigest()

    # 构造请求参数
    params = {
        'q': text,
        'from': from_lang,
        'to': to_lang,
        'appid': APP_ID,
        'salt': salt,
        'sign': sign
    }

    try:
        # 发送请求
        response = requests.get(url, params=params)
        result = json.loads(response.text)

        # 解析结果
        if 'trans_result' in result:
            translated = result['trans_result'][0]['dst']
            # 保持与原函数相同的后处理(虽然百度API通常不需要)
            return "".join(dict.fromkeys(translated.split())) if translated else ""
        else:
            print(f"翻译失败: {result.get('error_msg', '未知错误')}")
            return ""

    except Exception as e:
        print(f"请求翻译API时出错: {str(e)}")
        return ""
def translate_to_chi(text):
    if APP_ID=='' or SECRET_KEY=='':
        return translate_to_chi_local(text)
    return translate_to_chi_baidu(text)

from transformers import MarianMTModel, MarianTokenizer

model_name = "Helsinki-NLP/opus-mt-de-zh"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)


def translate_to_chi_local(text):
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
                words += ' '
                words += text
    return words


def process_words(txt, german_characters):
    word_count_dict = {}
    relib = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|", '\n', '\r', '\t', ':', ',', '.', '„', '“', '!', '#', '@',
             '~', '`', '\'', '&', '%', '^', '(', ')', '{', '}', '[', ']', '+', '=']
    for i in relib:
        txt = txt.replace(i, ' ')

    words = txt.split(' ')
    for word in words:
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
    german_characters = "äöüßÄÖÜẞabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_"
    if file_path.endswith(".pdf"):
        txt = extract_words_from_pdf(file_path)
    else:
        with open(file_path, 'r', encoding='utf-8') as file:
            txt = file.read()
    return process_words(txt, german_characters)


class Constants:
    New_ = 'Neue.md'
    Old_ = 'Alte.md'
    type1 = ' ' * 5
    type2 = ' ' * 10
    type3 = ' ' * 15
    UsedDictPath = 'used_dict.json'


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
    doc = nlp(deu)
    for sent in doc.sentences:
        for token in sent.tokens:
            for word_info in token.words:
                returns = InfoKopy(word_info.lemma, word_info.upos)
                return returns


class UsedDict:
    def __init__(self):
        self.path = os.path.join(os.getcwd(), Constants.UsedDictPath)

    def load(self):
        with open(self.path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def save(self, data):
        with open(self.path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)


class InfoKopy:
    def __init__(self, lemma, upos):
        self.lemma = lemma
        self.upos = upos


if __name__ == '__main__':
    deu = 'Nehmen'
    print(translate_to_chi(deu))
    print(classify(deu).upos)
    print(classify(deu).lemma)
