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

if __name__ == "__main__":
    # 获取 PDF 文件路径
    pdf_path = sys.argv[1]
    # 提取文本
    extracted_text = extract_words_from_pdf(pdf_path)

    # 将提取的文本转换为 JSON 并打印
    print(json.dumps(extracted_text))