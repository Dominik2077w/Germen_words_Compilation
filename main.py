
from file_processor import list_data_subdirectories, sort_subdirs_by_date  # 导入函数
import warnings
warnings.filterwarnings("ignore")  # 忽略所有警告

if __name__ == "__main__":
    list_data_subdirectories()