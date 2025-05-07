
# GWC项目逻辑分析报告

## 项目概述

“GWC”是一个用于处理德语资料的自动化工具，主要功能包括：

- **自动提取词汇**：从德语文本中收集词汇并进行词形还原（标准化处理）。
- **生成笔记**：对德语文本自动生成带有中文翻译的笔记，格式化输出。
- **分类词汇**：将提取的单词分类（动词、名词等）并附上中文翻译，以 Markdown 列表形式输出。

该项目采用层级化的结构来处理存储目录中的资料，通过调用深度学习接口（DeepSeek API）完成词性分析和笔记生成的工作。其总体流程为：扫描目录 → 逐文件/文件夹处理内容 → 调用 NLP 工具和API生成结果 → 输出 Markdown 和 PDF。

## 模块结构与作用

项目主要文件和模块包括：

- **main.py**：程序入口，调用 Project 类执行整个处理流程。用户需要在此脚本中指定待处理的根目录（Project(path)）。
- **project.py**：定义 Project 类，用于遍历根目录下的一级目录（可理解为课程或项目名称），对每个子目录执行处理。
    - **Project.__run__()**：对指定根目录下的每个文件夹调用 Folder，跳过隐藏目录（以.开头）。
- **folder.py**：定义 Folder 类，用于处理某个课程/项目目录。
  - **Folder.__run__(cutoff_date)**：获取该目录下所有子目录（视为“part”子模块），并对每个子目录按顺序调用 Part 类进行处理。
  - 维护一个集合 `folder_appeared_set` 记录已处理过的单词，避免跨子目录重复输出。
- **part.py**：定义 Part 类，用于处理具体的“部分”目录，可能包含多个文件或子文件夹。
  - **Part.__run__(cutoff_date)**：在给定目录下扫描所有内容项（文件或文件夹），过滤隐藏项和已有结果文件夹（名称由 Constants.Results_ 指定）。
  - 对于文件，调用 Xiaomi 类处理，获取该文件中的词汇集合。
  - 对于文件夹，调用 MinerU 类处理，获取其中的词汇集合。
  - 将各项返回的词汇合并到自身的 `current_set` 集合中。
  - 执行完扫描后，将新的词汇（`current_set - folder_appeared_set`）传给 `save_words_to_md`，生成该部分的新词汇 Markdown 文件 `Neue.md`。
  - 更新 `folder_appeared_set`，加入已处理过的单词，以便下一个子目录跳过这些词。
  - `save_words_to_md(words)`：对传入的词汇集合进行词形还原与分类，然后调用 GPT 风格接口生成格式化的 Markdown 文本，并保存到 `Neue.md`。
  - `save_md(md_text, filename)`：将生成的 Markdown 文本写入结果文件夹（Results）下的指定文件。
- **Xiaomi_file.py**：定义 Xiaomi 类，用于处理单个文本文件（假定为普通文本文件）。
  - **Xiaomi.__run__()**：读取指定文件的文本内容，调用 `deepseek_notizen_for_md_file` 函数生成笔记 Markdown。然后在该文件所在目录的 Results 子文件夹中新建同名 Markdown 文件，并将笔记写入。最后调用 `convert_md_to_pdf` 将 Markdown 转换为 PDF。
  - 返回该文件内容的词汇集合（通过 `read_text_and_get_set` 提取）。
- **MinerU_file.py**：定义 MinerU 类，用于处理包含结构化数据的文件夹，通常其中包含一个以 `_content_list.json` 结尾的 JSON 文件（可能是某种导出格式）。
  - `find_content_json()`：在指定文件夹及其子目录下查找 `_content_list.json` 文件路径，返回第一个找到的绝对路径。
  - **MinerU.__run__()**：若找到 JSON 文件，则创建 ContentJson 对象并执行 `__run__()`；否则打印未找到提示。返回最终的词汇集合。
  - 内部类 ContentJson：专门处理具体的 JSON 文件：
    - **ContentJson.__run__()**：读取 JSON 文件中的文本，调用 `deepseek_notizen_for_md_file` 生成笔记 Markdown，保存到上级目录的 Results 子文件夹中。最后将原始文本提取的词汇集合返回。
    - **ContentJson.read()**：实际读取 JSON 文件的内容并提取文本。若读取失败，会输出相应错误。
- **tools.py**：包含项目的各类工具函数和辅助逻辑。主要功能模块有：
  - 文本分块：`teilen_md_1200_in_string_list(text)` 将长文本分割为长度不超过 1200 字符的块，供多线程 API 调用。`teilen_words_250_in_str_list(words_set)` 将单词列表按每组不超过 250 个单词分割。
  - 深度学习调用：
    - `deepseek_notizen_for_md_file(text)`：对分块后的文本调用 `notize_word`（接口调用 DeepSeek API 的函数），收集各块返回的笔记 Markdown 片段，并用分割符拼接。
    - `deepseek_format_to_words_md(classified_words_set)`：对分类后的词汇列表调用 `format_word`（调用 DeepSeek API），获取格式化的词条 Markdown 行列表。
    - `notize_word(word, status)`：封装对 DeepSeek API 的调用，使用 PromptForNotizen 模板。
    - `format_word(word, status)`：封装对 DeepSeek API 的调用，使用 PromptForFormat 模板。
  - 词汇处理：`read_text_and_get_set(text)` 将文本按空格分词并过滤非德语字符，返回单词集合。`classify_words(words)` 使用 UsedDict 对每个单词进行词形还原（lemmas）并返回新集合。
  - 文件处理：`get_sorted_abs_part_subdir(abs_path)` 获取指定路径下的所有子目录（排除隐藏目录），并按名称排序返回全路径列表。
  - 输出辅助：`my_print1/2/3(txt, enter)` 用于在控制台打印带缩进的提示信息。`convert_md_to_pdf(md_path)` 将生成的 Markdown 文件调用外部工具 markdown-pdf 转换为同名 PDF。
  - 缓存机制：项目使用 UsedDict 缓存词汇还原结果（存储在 `used_dict.json`）和 DeepSeekCache 缓存 API 请求结果（存储在 `deepseek_cache.json`），减少重复计算和请求。
- **myhttp.py**：处理与 DeepSeek API 相关的网络请求。
  - 使用 requests 和 requests_cache 实现对 DeepSeek 接口的访问，并通过多线程 (`process_array`) 并发加速处理。
  - **DeepSeekCache 类**：实现对 DeepSeek API 调用结果的本地缓存，可保存/加载 JSON 文件。
  - `ask_deepseek(prompt, text, status)`：向 https://api.deepseek.com/v1/chat/completions 发送请求，携带指定的系统提示（Prompt）和文本，获取 AI 返回的内容。先检查内存缓存 `deepSeekCache`，若命中则直接返回，否则发起新请求并将结果缓存。支持自动重试限流错误（HTTP 429）。
  - `process_array(array, func)`：对列表元素并发地应用 `func` 函数，`func` 接受（item, status）参数，并返回结果。最后收集所有结果并保存缓存。
- **Const.py**：定义常量和配置。
  - 路径常量：`BASE_DIR`（程序运行目录）、`Results_`（结果子文件夹名）、`New_/Old_`（新旧词汇文件名）。
  - API 密钥：`DEEPSEEK_API_KEY`（需替换为用户自己的 DeepSeek API Key）。
  - 缓存路径：`USED_DICT_PATH`、`DEEPSEEK_CACHE_PATH` 指向缓存 JSON 文件位置。
  - Prompt 模板：`PromptForNotizen`（生成双语笔记的提示语）和 `PromptForFormat`（词汇分类和翻译的提示语），均为中文指令格式，以指导 AI 模型输出要求的格式。

## 数据流程

1. 项目启动：`main.py` 中的 `Project(path).__run__()` 方法被调用，其中 `path` 为根目录绝对路径或相对路径。
2. 顶层目录遍历：`Project.__run__()` 遍历根目录下的每个文件夹（忽略隐藏文件夹）。对于每个文件夹，创建 Folder 实例并调用其 `__run__()` 方法。
3. 处理“课程/项目”文件夹：`Folder.__run__()` 打印当前目录信息，并调用 `get_sorted_abs_part_subdir` 获取该目录下排序后的所有子文件夹路径。对于每个子文件夹，创建 Part 实例（传入当前文件夹维护的单词集合）并执行 `__run__()`。
4. 扫描“部分”目录：`Part.__run__()` 中，列出目录下所有可见项目（文件或子目录）。
   - 如果是文件：调用 `Xiaomi(full_path).__run__()`。Xiaomi 读取文本、生成笔记并保存文件，同时返回该文本的词汇集合。
   - 如果是文件夹：调用 `MinerU(full_path).__run__()`。MinerU 在该文件夹内查找 `_content_list.json` 并创建 ContentJson 处理它；ContentJson 读取 JSON 文本、生成笔记并保存文件，同时返回文本的词汇集合。
   - 将每个子任务返回的词汇并入 Part 的 `current_set` 集合。
5. 词汇去重与保存：遍历结束后，Part 计算新增词汇 `new_words = current_set - folder_appeared_set`。
   - 对这些 `new_words` 调用 `classify_words`（词形还原）和 `deepseek_format_to_words_md`（AI 格式化为 Markdown 列表）生成内容。
   - 将生成的 Markdown 文本写入 `Results/Neue.md` 文件。
   - 更新 `folder_appeared_set`，加入 `current_set` 中的所有词，以备下一个子目录跳过已出现过的词。
6. 笔记文件生成：对于每个被处理的文件或 JSON 内容，Xiaomi 和 ContentJson 会调用 `deepseek_notizen_for_md_file` 生成笔记 Markdown，并保存到对应目录的 Results 文件夹，同时将该 Markdown 转换为 PDF。
7. 输出结果：最终，在每个“部分”目录下的 Results 文件夹里产生：
   - `Neue.md`：新增词汇列表（Markdown 格式）。
   - 对应的笔记 Markdown (.md) 文件：由同名源文件生成。
   - 若外部工具可用，还将生成同名 PDF 文件。

## 核心算法与逻辑

- **文本切分与并发处理**：由于 API 对请求长度有限制，`deepseek_notizen_for_md_file` 将长文本分割成不超过1200字符的块，`deepseek_format_to_words_md` 将词汇列表分割成最多250词的块。然后使用多线程（`process_array`）并发请求 DeepSeek API，加快处理速度，并在结束后统一保存缓存。
- **词形还原与分类**：使用斯坦福的 Stanza 库 (`stanza.Pipeline`)，在 `classify(deu)` 函数中对德语单词进行分词和词形还原（获取词根）。UsedDict 类实现缓存，将已处理过的词形还原结果保存在 `used_dict.json`，避免重复计算。
- **深度学习接口调用**：通过 DeepSeek 的 Chat Completion API（类似 OpenAI 的 ChatGPT），根据预设的中文提示 (`PromptForNotizen`、`PromptForFormat`) 生成所需内容：
  - `PromptForNotizen`：告诉模型将德语文本转换成双语笔记，要求保留 LaTeX 数学公式，加粗重要词汇，在文本前分别加上 [德文] 和 [中文]。
  - `PromptForFormat`：告诉模型将德语单词分类（动词、名词、形容词/副词、专有名词）并翻译成中文，要求逐行输出 Markdown 列表。
- **结果缓存**：DeepSeekCache 类缓存所有的 API 请求结果到 `deepseek_cache.json`。在调用 `ask_deepseek` 时，先检查是否已有缓存，若有则直接返回，减少网络请求次数和成本。
- **外部工具调用**：将生成的 Markdown 文件转为 PDF 时，`convert_md_to_pdf` 函数调用系统命令 `markdown-pdf`（需要用户自行安装该工具）来完成转换，并输出结果状态。

整体来看，该项目通过清晰的模块分工，实现了自动化的目录扫描、内容处理、词汇提取和深度学习辅助的笔记/词汇生成。数据在各层级以集合形式累积词汇，通过分类和差集运算去重；通过多线程和缓存提高了API调用效率；同时生成易读的 Markdown 笔记和词汇表，便于后续查看和归档。

---

# GWC用户使用手册

## 安装指南

1. **准备Python环境**：确保系统已安装 Python 3（建议 3.7+）。打开终端/命令提示符。
2. **获取项目文件**：将 GWC.zip 解压到本地任意目录（下称“安装目录”）。
3. **安装依赖库**：在安装目录打开终端，运行：
   ```bash
   pip install -r requirements.txt
   ```
   这会安装项目所需的第三方库（包括 requests, stanza, requests-cache, Markdown, weasyprint 等）。
4. **配置 API 密钥**：程序使用 DeepSeek 接口生成笔记和词汇说明。您需要注册获取 DeepSeek API Key，并将其填入 `Const.py` 文件中的 `DEEPSEEK_API_KEY` 字段，替换默认占位符。
5. **安装 Markdown-to-PDF 工具（可选）**：程序调用外部命令 `markdown-pdf` 将 Markdown 转为 PDF。如果您希望生成 PDF，需要安装此工具（通常通过 Node.js 安装）：
   ```bash
   npm install -g markdown-pdf
   ```

## 使用方式

1. **准备资料**：将待处理的德语资料按如下结构构建：
   **note是小米15同声传译导出的md字幕文件，MinerU是开源工具MinerU解析pdf文件导出的文件夹**
   ```
   Project/
   │
   ├─ Folder_A/  
   │   ├─ Part_1/  
   │   │   ├─ note1.md  
   │   │   ├─ note2.md 
   │   │   └─ MinerU/
   │   │       └─ _content_list.json
   │   └─ Part_2/  
   │       └─ ^^^^^^ 
   │
   └─ Folder_B/  
      └─ Part_1/  
         ├─ ^^^^^^^^
         └─ ^^^^^^
   ```
2. **启动程序**，有两种方式，一种是 `Project("你的Project目录的绝对地址").run()`，对所有的课程进行处理。另一种是 `Folder("你的Folder目录的绝对地址").run()`，对指定的课程进行处理。
3. **得到结果**：
   ```
   Project/
   │
   ├─ Folder_A/  
   │   ├─ Part_1/  
   │   │   ├─ note1.md  
   │   │   ├─ note2.md 
   │   │   ├─ MinerU/
   │   │   │  └─ _content_list.json
   │   │   └ Results/
   │   │      ├─ Neue.md
   │   │      ├─ note1.md
   │   │      ├─ note1.pdf(可选)
   │   │      ├─ MinerUXXX.md
   │   │      ├─ MinerUXXX.pdf(可选)
   │   │      ├─ note2.pdf(可选)
   │   │      └─ note2.md
   │   │      
   │   └─ Part_2/  
   │       └─ ^^^^^^ 
   │
   └─ Folder_B/  
      └─ Part_1/  
         ├─ ^^^^^^^^
         └─ ^^^^^^
   ```
   按照以上说明正确安装并运行后，GWC 将自动生成每个部分的双语笔记和词汇列表文件，您可以直接查看 Results 文件夹中的 Markdown 或 PDF 文档。祝您使用顺利！

## 项目初衷，历程

- 这个项目的起因是，2个月的德国留学造成的需求。
- 历程可以归类成三种因素：
  - 需求
  - 限制
  - 结果

1. 刚开始：
   - **需求**：想知道老师嘴巴里说的我们没学过的词。
   - **限制**：小米15的同声传译免费而且准确度无敌高。
   - **结果**：我们采用了小米15的同声传译，来获得字幕。

2. 之后：
   - **需求**：想在课后能找到那些生词。
   - **限制**：手动抄录整理生词，或是去翻字幕文件也太傻了。
   - **结果**：我们开发了第一版项目，使用python脚本和自然语言库。提取归类出每个科目每节课的新词。

3. 最近：
   - **需求**：单词背的差不多了，但是课件里的固定搭配看不太懂，一个一个查好麻烦。以及想学习课堂老师的口语表达
   - **限制**：提取固定搭配和理解语义，目前只有AI能做到。DeepSeek V3价格便宜。而且网络请求需要并发。
   - **结果**：我们开发了第二版项目，使用Go语言和DeepSeek V3 API。提取归类出每个科目每节课的固定搭配和老师的口语表达


### 祝大家，开心:D

可以通过转账狠狠的奖励我吗[doge]

有什么问题或建议，欢迎随时交流！

联系邮箱：`< Dominik_For_Heybox@163.com >`
## 以下是各种实例图：
![截屏2025-05-06 01.34.38.png](Cache/%E6%88%AA%E5%B1%8F2025-05-06%2001.34.38.png)
![截屏2025-05-07 16.56.55.png](Cache/%E6%88%AA%E5%B1%8F2025-05-07%2016.56.55.png)
![截屏2025-05-07 16.57.20.png](Cache/%E6%88%AA%E5%B1%8F2025-05-07%2016.57.20.png)
![截屏2025-05-07 16.57.56.png](Cache/%E6%88%AA%E5%B1%8F2025-05-07%2016.57.56.png)
![截屏2025-05-07 16.58.29.png](Cache/%E6%88%AA%E5%B1%8F2025-05-07%2016.58.29.png)
![截屏2025-05-07 16.59.20.png](Cache/%E6%88%AA%E5%B1%8F2025-05-07%2016.59.20.png)
![截屏2025-05-07 16.59.26.png](Cache/%E6%88%AA%E5%B1%8F2025-05-07%2016.59.26.png)
![截屏2025-05-07 16.59.55.png](Cache/%E6%88%AA%E5%B1%8F2025-05-07%2016.59.55.png)