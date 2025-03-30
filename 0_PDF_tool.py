from PyPDF2 import PdfReader, PdfWriter
from typing import List
import os


def split_pdf(pdf_path: str, page_numbers: List[int]) -> None:
    """
    根据指定页码分割PDF文件

    :param pdf_path: PDF文件路径
    :param page_numbers: 分割点的页码列表(从1开始)
    """
    try:
        # 打开PDF文件
        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)

        # 验证页码
        if not page_numbers or max(page_numbers) > total_pages:
            raise ValueError("页码超出范围")

        # 确保页码有序且包含文件结尾
        split_points = sorted(set(page_numbers))
        if split_points[-1] != total_pages:
            split_points.append(total_pages)

        # 获取原文件名（不含扩展名）
        base_name = os.path.splitext(pdf_path)[0]

        # 分割处理
        start_page = 0
        for i, end_page in enumerate(split_points, 1):
            writer = PdfWriter()

            # 添加页面到新文件
            for page_num in range(start_page, end_page):
                writer.add_page(reader.pages[page_num])

            # 保存新文件
            output_path = f"{base_name}_part{i}.pdf"
            with open(output_path, "wb") as output_file:
                writer.write(output_file)

            start_page = end_page

        

    except Exception as e:
        

if __name__ == "__main__":
    # 示例用法
    pdf_path = "Cashes/WiRecht_SoSe_25_§ 1-§ 4 (BGB AT).pdf"  # 替换为你的PDF文件路径
    page_numbers = [16]  # 替换为你想要分割的页码列表
    split_pdf(pdf_path, page_numbers)


