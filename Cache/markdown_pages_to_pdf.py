import json
import sys

from markdown2 import markdown
from weasyprint import HTML, CSS
def markdown_pages_to_pdf(output_path, md_list):
    """
    将多个 Markdown 字符串按页渲染为 PDF，并输出到指定路径。

    参数：
    - md_list: Markdown 字符串列表
    - output_path: 输出 PDF 文件路径
    """
    css = CSS(string="""
        @page { margin: 40px; }
        body {
            font-family: 'Helvetica', 'Arial', 'Microsoft YaHei', '微软雅黑', 
                        'PingFang SC', '苹方', 'STHeitiSC-Light', 
                        'Noto Sans CJK SC', sans-serif;
            line-height: 1.6;
        }
        h1, h2, h3 {
            color: #2E86C1;
        }
        pre {
            background-color: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }
    """)

    # 转换每段 Markdown 为单独的 HTML 页
    documents = []
    for md in md_list:
        html = markdown(md)
        doc = HTML(string=html).render(stylesheets=[css])
        documents.append(doc)

    # 合并所有渲染后的页面
    all_pages = []
    for doc in documents:
        all_pages.extend(doc.pages)

    # 输出为最终 PDF
    if all_pages:
        documents[0].copy(all_pages).write_pdf(output_path)
        print(json.dumps("OK"))
    else:
        print(json.dumps("NO"))
if __name__== "__main__":
    # 获取 Markdown 文件路径
    pdf_path = sys.argv[1]
    mdStringList = json.loads(sys.argv[2])



    # 调用函数生成 PDF
    markdown_pages_to_pdf(pdf_path, mdStringList)