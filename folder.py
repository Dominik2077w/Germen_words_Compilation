from part import Part
from tools import *


class Folder:
    def __init__(self, rel_path):
        self.rel_path = rel_path
        self.abs_path = os.path.join(Constants.BASE_DIR, rel_path)
        self.folder_appeared_set = set()

    def __run__(self, cutoff_date='        ALL'):
        # EmailAddress: Dominik_For_Heybox@163.com  有什么问题和需求可以联系
        # 前五个给这个邮箱发送邮件的学弟学妹有机会获得，请学长吃饭的机会:D  [doge]
        my_print1(f'{self.rel_path} from {cutoff_date} to now', 1)
        sorted_abs_part_subdir = get_sorted_abs_part_subdir(self.abs_path)
        for subdir in sorted_abs_part_subdir:
            Part(subdir, self.folder_appeared_set).__run__(cutoff_date)
