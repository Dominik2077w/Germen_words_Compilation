# 德语生词自动整理工具 📚➡️📖

## 项目初衷 ✨
解决德语课堂中的常见痛点：
- 课堂上频繁遇到新单词，但没时间即时记录和查阅
- 实时翻译字幕（如小米同传）无法课后高效复习
- 本工具自动从课件/字幕中提取**首次出现**的生词，生成可复习的词表

## 核心功能
- 🚀 自动比对新旧课程材料中的词汇差异
- 🔍 智能分离「新词」与「已学词」
- 🌍 支持DeepL/百度API翻译（需自行申请）
- 📅 按课程日期自动归档
- 📂 结构化输出Markdown文件

---

## 快速开始

### 1. 下载项目
```bash
git clone https://github.com/Dominik2077w/Germen_words_Compilation.git
```
或直接下载ZIP包（点击GitHub页面的"< > Code" → "Download ZIP"）

### 2. 环境配置
- 1.用IDE打开项目（推荐PyCharm学生版）

- 2.使用Python 3.12（3.13有兼容问题）

- 3.安装依赖：

```bash
pip install -r requirements.txt
```
### 3. 配置翻译API
在Methode.py中填写：

- 支持DeepL（需银行卡）或百度翻译（需手机号）

- 不配置API将使用本地翻译模型（效果较差）

### 4. 准备课程文件
按此结构整理文件：

```复制
项目目录/
└── 课程主题/          # 如「MARK」
    └── 上课日期/      # 如「20231001」
        ├── 课件/      # PDF/PPT等
        └── 字幕/      # SRT/VTT等
```
文件夹结构示例:

![img.png](Cashes/img3.png)

## 使用方法
### 方式一：覆盖处理所有课程项目
```python
from Object import Project
Project('Data').__run__()  # 处理Data目录下所有内容
```
### 方式二：处理单个课程项目
```python
from Object import Folder
# 只处理2023年10月后的课程
Folder('Data/MARK').__run__("20231001")  
# 或处理全部历史课程
Folder('Data/MARK').__run__()
```
## 生成文件
每个课程日期文件夹中将出现：

- ***neue.md***：新出现的词汇（之前课程未出现过）

- ***alte.md***：已学过的词汇

输出文件示例

## 技术细节
数据处理流程:

![img1.png](Cashes/img1.png)

## 使用建议
- 搭配Obsidian词典插件或「德语助手」复习效果更佳

- 中文翻译仅供参考

- 已处理词汇保存在used_dict.json中,可供后续使用,不会一直调用API

## 灵感池 💡
Scheißtag

如果你看到这里，但是还不会用的话，可以在release中下载最新的打包文件文件，直接运行就可以了:D

### 今日状态：🌱 轻松 | 🎨 创意 | ⏳ 等待灵感
