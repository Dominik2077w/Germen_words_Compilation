import os
import sys
from pathlib import Path


def get_base_dir():
    """获取可执行文件所在目录"""
    if getattr(sys, 'frozen', False):
        # 打包后：sys.executable 是可执行文件路径
        return Path(os.path.dirname(sys.executable))
    else:
        # 开发时：返回当前脚本目录
        return Path(os.path.dirname(os.path.abspath(__file__)))


class Constants:
    New_ = 'Neue.md'
    Old_ = 'Alte.md'
    Results_ = 'Results'
    type1 = ' ' * 5
    type2 = ' ' * 10
    type3 = ' ' * 15
    BASE_DIR = get_base_dir()
    CACHE_DIR = BASE_DIR / 'Cashes'
    DEEPSEEK_API_KEY = 'sk-8f5badd481c4492883dd2904d98a6a9a'  # 替换

    # File paths
    USED_DICT_PATH = CACHE_DIR / 'used_dict.json'
    DEEPSEEK_CACHE_PATH = CACHE_DIR / 'deepseek_cache.json'
    PromptForNotizen ="""请将以下提供的文本进行处理，然后直接返回处理后的文本，保存完整的LaTeX 数学命令，LaTeX 数学命令中的文本不需要加工！！!但是修改 LaTeX 语法，改为现代写法。其余无需回复。加工要求：加粗标出输入的德语文本中的口语表达/固定搭配/重要词汇，并括号跟上中文翻译。比如说***口语表达/固定搭配/重要词汇***(中文翻译)。下面再搭一整段中文翻译，口语表达/固定搭配/重要词汇也要加粗标出，以及括号配上德语原文。两段文本的开头分别加上[德文][中文]。下面是要处理的文本:\n"""

    PromptForFormat = """请将以下提供的德语单词区分出动词、名词、形容词副词，专有名词，分析并填入下列模版，以Markdown格式返回。要求：  
1. 名词需标注词性（der/die/das）  
2. 所有单词提供中文翻译  
3. 仅返回结果，不要添加任何额外的文字或解释，也不要添加任何形式的文本格式框。
4. 每一行是一个单词按以下格式返回：
- (Verben)/(Nomen)/(Adjektive)/(Adverbien)/(Eigennamen) der/die/das(如果是名词的话) 单词 - 翻译
- …………
- …………

以下是待处理单词：
"""


Constants.CACHE_DIR.mkdir(exist_ok=True)  # 确保目录存在
