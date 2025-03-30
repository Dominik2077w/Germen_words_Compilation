from file_processor import sort_subdirs_by_date

if __name__=="__main__":
    # 示例用法
    relative_path = "Data/Test"  # 替换为你的相对路径
    cutoff_date = "20150405"  # 替换为你的截止日期
    sort_subdirs_by_date(relative_path)