import warnings
from typing import Dict, Set

warnings.filterwarnings("ignore")  # 忽略所有警告
import stanza

try:
    stanza.download('de')
    nlp = stanza.Pipeline('de', processors='tokenize,mwt,pos,lemma,ner')
except Exception:
    nlp = None


def classify_german_words(word_set: Set[str]) -> Dict[str, Set[str]]:
    global nlp
    if nlp is None:
        raise RuntimeError("请先安装德语模型，运行命令: stanza.download('de')")

    categories = {'entities': set()}

    for word in word_set:
        doc = nlp(word.lower())
        for sent in doc.sentences:
            for token in sent.tokens:
                for word_info in token.words:
                    lemma = word_info.lemma
                    pos = word_info.upos
                    if pos == 'NOUN':
                        lemma = lemma.capitalize()
                    ner = token.ner if hasattr(token, 'ner') else 'O'

                    # 动态词性分类
                    if pos not in categories:
                        categories[pos] = set()
                    categories[pos].add(lemma)

                    # 命名实体识别
                    if ner != 'O':
                        categories['entities'].add(lemma)

    return categories


def classify_german_old_words(word_set: Set[str], history) -> Dict[str, Set[str]]:
    categories = {'entities': set()}

    for word in word_set:
        doc = history[word]
        for sent in doc.sentences:
            for token in sent.tokens:
                for word_info in token.words:
                    lemma = word_info.lemma
                    pos = word_info.upos
                    if pos == 'NOUN':
                        lemma = lemma.capitalize()
                    ner = token.ner if hasattr(token, 'ner') else 'O'

                    # 动态词性分类
                    if pos not in categories:
                        categories[pos] = set()
                    categories[pos].add(lemma)

                    # 命名实体识别
                    if ner != 'O':
                        categories['entities'].add(lemma)

    return categories


def classify_german_new_words(word_set: Set[str], history) -> Dict[str, Set[str]]:
    global nlp
    if nlp is None:
        raise RuntimeError("请先安装德语模型，运行命令: stanza.download('de')")

    categories = {'entities': set()}
    cNum = 0
    tNum = len(word_set)
    for word in word_set:
        doc = nlp(word.lower())
        history[word] = doc
        for sent in doc.sentences:
            for token in sent.tokens:
                for word_info in token.words:
                    lemma = word_info.lemma
                    pos = word_info.upos
                    if pos == 'NOUN':
                        lemma = lemma.capitalize()
                    ner = token.ner if hasattr(token, 'ner') else 'O'
                    print(f"\r                                                                                                            ",
                          end="", flush=True)

                    print(f"\r                *classify process({cNum}/{tNum})[{word}==>{lemma} {pos} {ner}]", end="", flush=True)
                    cNum += 1

                    # 动态词性分类
                    if pos not in categories:
                        categories[pos] = set()
                    categories[pos].add(lemma)

                    # 命名实体识别
                    if ner != 'O':
                        categories['entities'].add(lemma)
    print()
    return categories


from transformers import MarianMTModel, MarianTokenizer

model_name = "Helsinki-NLP/opus-mt-de-zh"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)


def translate_german_to_chinese(text):
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


def get_german_gender(word: str) -> str:
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


def format_classification_to_md(classified_dict: Dict[str, Set[str]]) -> str:
    """
    将分类结果格式化为Markdown文本
    :param classified_dict: classify_german_words返回的分类字典
    :return: 格式化后的Markdown字符串
    """
    md_content = []

    # 按指定顺序处理分类
    ordered_categories = ['entities'] + sorted([cat for cat in classified_dict if cat != 'entities'])
    for category in ordered_categories:
        words = classified_dict.get(category, set())
        if not words:
            continue

        display_name = category.upper() if category != 'entities' else 'Entities'
        md_content.append(f'## {display_name}')

        for word in sorted(words):
            gender_str = f"{get_german_gender(word)} " if category == 'NOUN' else ""
            translated = translate_german_to_chinese(word)
            line = f'- {gender_str}{word} {translated}'
            md_content.append(line)

        md_content.append('')  # 添加空行分隔
    return '\n'.join(md_content).strip()


def format_new_classification_to_md(classified_dict: Dict[str, Set[str]], history) -> str:
    """
    将分类结果格式化为Markdown文本
    :param history:
    :param classified_dict: classify_german_words返回的分类字典
    :return: 格式化后的Markdown字符串
    """
    md_content = []

    # 按指定顺序处理分类
    ordered_categories = ['entities'] + sorted([cat for cat in classified_dict if cat != 'entities'])
    tNum = 0
    for category in ordered_categories:
        for j in classified_dict[category]:
            tNum += 1

    cNum = 0
    for category in ordered_categories:
        words = classified_dict.get(category, set())
        if not words:
            continue

        display_name = category.upper() if category != 'entities' else 'Entities'
        md_content.append(f'## {display_name}')

        for word in sorted(words):
            gender_str = f"{get_german_gender(word)} " if category == 'NOUN' else ""
            translated = translate_german_to_chinese(word)
            line = f'- {gender_str}{word} {translated}'
            history[word] = line
            print(f"\r                                                                                                            ", end="",
                  flush=True)
            print(f"\r                *translate process({cNum}/{tNum})[{line}]", end="", flush=True)
            cNum += 1

            md_content.append(line)

        md_content.append('')  # 添加空行分隔
    print()
    return '\n'.join(md_content).strip()


def format_old_classification_to_md(classified_dict: Dict[str, Set[str]], history) -> str:
    """
    将分类结果格式化为Markdown文本
    :param history:
    :param classified_dict: classify_german_words返回的分类字典
    :return: 格式化后的Markdown字符串
    """
    md_content = []

    # 按指定顺序处理分类
    ordered_categories = ['entities'] + sorted([cat for cat in classified_dict if cat != 'entities'])
    for category in ordered_categories:
        words = classified_dict.get(category, set())
        if not words:
            continue

        display_name = category.upper() if category != 'entities' else 'Entities'
        md_content.append(f'## {display_name}')

        for word in sorted(words):
            line = history[word]
            md_content.append(line)

        md_content.append('')  # 添加空行分隔
    return '\n'.join(md_content).strip()


if __name__ == "__main__":
    le_set = {'Haus', 'Auto', 'Hund', 'Entwicklung', 'entwicklung'}
    classified = classify_german_words(le_set)
