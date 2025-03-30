import os
import time
from datetime import datetime

from nlp_processor import classify_german_new_words, \
    classify_german_old_words, format_new_classification_to_md, format_old_classification_to_md
from process_text import from_md_to_germen_set, extract_unique_german_words


def list_data_subdirectories():
    """
    遍历项目Data目录下的所有子目录，并打印相对路径
    """
    base_dir = os.path.join(os.getcwd(), 'Data')
    try:
        for entry in os.listdir(base_dir):
            full_path = os.path.join(base_dir, entry)
            if os.path.isdir(full_path):
                rel_path = os.path.relpath(full_path, os.getcwd())
                print(rel_path)
                sort_subdirs_by_date(rel_path)
    except FileNotFoundError:
        os.makedirs(base_dir, exist_ok=True)
        print(f"目录 {base_dir} 已自动创建")


def sort_subdirs_by_date(relative_path, cutoff_date="19491001"):
    """
    按日期排序指定目录下的子文件夹
    :param relative_path: 相对于项目根目录的路径
    :param cutoff_date: 截止日期（YYYYMMDD格式），默认19491001
    """
    target_dir = os.path.join(os.getcwd(), relative_path)

    cutoff_date_obj = datetime.strptime(cutoff_date, "%Y%m%d")

    print(f"{relative_path}--->{cutoff_date_obj}:")
    try:
        subdirs = [d for d in os.listdir(target_dir)
                   if os.path.isdir(os.path.join(target_dir, d))]

        dated_dirs = []
        for d in subdirs:
            if len(d) < 8:
                continue
            date_str = d[:8]
            try:
                date = datetime.strptime(date_str, "%Y%m%d")
                dated_dirs.append((date, d))  # 保留原始目录名
            except ValueError:
                continue

        sorted_dirs = sorted(dated_dirs, key=lambda x: x[0])  # 按日期对象排序
        history_unclassified_set = set()
        used_dict_for_classify = dict()
        used_dict_for_translate = dict()
        for date_obj, dir_name in sorted_dirs:
            full_path = os.path.join(target_dir, dir_name)
            print(" "*5 + "~/",dir_name)
            time.sleep(0.1)
            md_file = os.path.join(full_path, "Neue_Wörter.md")
            if date_obj < cutoff_date_obj:
                try:
                    words = extract_unique_german_words(md_file)
                    print(" "*5+"- ","get_new_words:", len(words))
                    time.sleep(0.1)
                    history_unclassified_set.update(words)
                    print(" " * 5 + "- ", "classify_new_words:", len(words))
                    time.sleep(0.1)
                    temp_formated_dict = classify_german_new_words(words, used_dict_for_classify)
                    print(" " * 5 + "- ", "translate_new_words:", len(words))
                    time.sleep(0.1)
                    format_new_classification_to_md(temp_formated_dict, used_dict_for_translate)
                except FileNotFoundError:
                    print(f"警告：{md_file} 文件不存在")
            else:
                current_unclassified_set = from_md_to_germen_set(full_path)
                print(" " * 10 + "- fetched",len(current_unclassified_set),"words")
                new_dict_for_md = classify_german_new_words(current_unclassified_set - history_unclassified_set,
                                                            used_dict_for_classify)
                old_dict_for_md = classify_german_old_words(current_unclassified_set & history_unclassified_set,
                                                            used_dict_for_classify)
                new_formate_dict_for_md = format_new_classification_to_md(new_dict_for_md, used_dict_for_translate)
                old_formate_dict_for_md = format_old_classification_to_md(old_dict_for_md, used_dict_for_translate)

                save_md(full_path, new_formate_dict_for_md, "Neue_Wörter")
                save_md(full_path, old_formate_dict_for_md, "Alte_Wörter")

                history_unclassified_set.update(current_unclassified_set)

    except FileNotFoundError:
        print(f"错误：{target_dir} 目录不存在")
    except NotADirectoryError:
        print(f"错误：{target_dir} 不是有效目录")


def save_md(relative_path, data_set, filename):
    """
    将集合数据保存到指定路径的Markdown文件
    :param relative_path: 相对于项目根目录的路径
    :param data_set: 要保存的数据集合
    :param filename: 目标文件名（自动添加.md后缀）
    """
    target_dir = os.path.join(os.getcwd(), relative_path)

    # 确保文件名以.md结尾
    if not filename.lower().endswith('.md'):
        filename += '.md'

    try:
        # 创建目标目录（如果不存在）
        os.makedirs(target_dir, exist_ok=True)

        # 构建完整文件路径
        file_path = os.path.join(target_dir, filename)

        # 写入集合数据
        with open(file_path, 'w', encoding='utf-8') as f:

            f.write(data_set)

        print(" " * 10 + "- ",f"{filename} saved")

    except Exception as e:
        print(f"保存文件失败: {str(e)}")
