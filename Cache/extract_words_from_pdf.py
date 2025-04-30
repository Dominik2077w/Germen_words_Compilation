import json
import logging
import warnings
import sys
import pdfplumber

def extract_words_from_pdf(pdf_path0):
    logging.getLogger('pdfminer').setLevel(logging.ERROR)

    text = []
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=UserWarning)

        with pdfplumber.open(pdf_path0) as pdf:
            for page in pdf.pages:
                text.append(page.extract_text(x_tolerance=1))
    return text


def extract_words_from_plain_words(pdf_path0):
    lines= []
    with open(pdf_path0, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    ans=[]
    cur=''
    for line in lines:
        if line=="":
            continue
        if len(cur)<=500:
            cur+="\n"+line
        else:
            ans.append(cur)
            cur=line
    if cur:
        ans.append(cur)
    return ans




def extract_words(pdf_path0):
    if pdf_path0.endswith('.pdf'):
        return extract_words_from_pdf(pdf_path0)
    elif pdf_path0.endswith('.md')or pdf_path0.endswith('.txt'):
        return extract_words_from_plain_words(pdf_path0)
    else:
        raise ValueError("Unsupported file type. Please provide a .pdf or .md file.")



if __name__ == "__main__":
    # 获取 PDF 文件路径
    pdf_path = sys.argv[1]
    # 提取文本
    extracted_text = extract_words(pdf_path)

    # 将提取的文本转换为 JSON 并打印
    print(json.dumps(extracted_text))