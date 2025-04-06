## 制作初衷 ✨
- 原因在德语课堂上会遇到新的没有见过的单词，但是课堂上很难有时间去记录和查阅。(就算用同声传译也很难标记下来，谁会课后去看字幕呢？)
- 于是我们尝试，课堂上用小米手机同声传译纯看德语字幕。课后导出字幕文件，结合课堂上使用的资料文件，自动化地提取出课堂新出现的单词。以供复习。
## 如何下载
```
- 网址:https://github.com/Dominik2077w/Germen_words_Compilation.git
- 或使用命令 git clone https://github.com/Dominik2077w/Germen_words_Compilation.git
```
## 依赖库
```
pip install -r requirements.txt #使用Python 3.12, Python 3.13有兼容问题
```


## 使用步骤
- 1 .使用者应该按照如图结构在python项目目录下构建自己的文件夹结构，并将资料文件(md/非扫描版pdf)放入对应文件夹!
- ![img.png](Cashes/img.png)
- 2 .启动程序，等待完成计算。
- ![img_1.png](Cashes/img_1.png)
- 3 .计算完成后，对应目录下会生成neue_wörter文件与alte_wörter文件
- ![img_2.png](Cashes/img_2.png)
- 4 .示例neue_wörter文件:
- ![img_3.png](Cashes/img_3.png)
## 主要结构——提供了三个类，分别对应了Project层，Folder层和Part层
- Project类：接收一个相对目录地址，创建一个Project对象。可以遍历读取其中的所有子Folder目录名，依次创建Folder对象。
- Folder类：接收一个相对目录地址，创建一个Folder对象。可以遍历读取其中的所有子Part目录名，依次创建Part对象，负责在同一个Folder中的多个Part对象之间传递信息。
- Part类：接收一个绝对目录地址，创建一个Part对象。可以读取其中的所有md文件和pdf文件，负责信息加工和文件读写。
## 逻辑细节
- folder级别的文件夹之间是相互独立的，互不影响
- 计算得到的neue_wörter.md文件中，(记录了当前part文件夹中存在的，并且在更早的part文件夹中没有存在过的)词汇。并汇总成了序列。
- 计算得到的alte_wörter.md文件中，(记录了当前part文件夹中存在的，并且在更早的part文件夹中已经存在过的)词汇。并汇总成了序列。
## 启动方式
- 1 . 通过Project类的__init__方法，传入一个本项目的通向Project层目录的相对路径(比如说Data)，创建一个Project对象，对全局重新计算以及覆盖保存
```
from Object import Project

if __name__ == "__main__":
    Project('Data').__run__()
```
- 2 . 通过Folder类的__init__方法，传入一个本项目的通向Folder层目录相对路径(比如说Data/MARK)，创建一个Folder对象，并传入一个字符串参数(比如说20231001)，对这个文件夹下的所有在输入字符串参数日期之后的Part目录进行重新计算和覆盖保存。
```
from Object import Folder

if __name__ == '__main__':
    Folder('Data/MARK').__run__("20231001")
```
## 使用实例
- 1 . 建立了“课程结构——某节课”结构的的文件夹；第一个part文件夹导入了来自德语助手的基础词汇六百词，用来把简单词汇截流下来 :
- ![img_4.png](Cashes/img_4.png)
## 碎碎念
- 为什么只接受非扫描版pdf文件和markdown文件？因为我们在课上用的是小米自带的同声传译，导出后的字幕文件是markdown。以及我们的Moodle课件都是非扫描版pdf。如果你有别的需求，可以自己增加几个读取文档的函数。
- 录音文件和字幕文件，是小米手机在课堂上同声传译的。
- 这些处理好的单词序列能用来做什么呢，这取决于你的想法。我一般结合Obsidian的词典插件或者德语助手来使用。 
- 单词的中文翻译仅供参考
## 灵感池 💡
- Schöntag
- Scheißtag

## 今日心情

🌱 轻松 | 🎨 创意 | ⏳ 等待灵感
