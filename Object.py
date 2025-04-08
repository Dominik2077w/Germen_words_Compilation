import os
import warnings

from Methode import classify, count_dict_add, get_sorted_abs_part_subdir, Constants, count_dict_add_dict, \
    extract_word_dict_from_docx, MdFormat, get_noun_gender, my_print1, my_print2, my_print3, UsedDict, \
    translate_to_chi, translate_to_chi1

warnings.filterwarnings("ignore")  # 忽略所有警告


class Project:
    def __init__(self, project_name):
        self.project_name = project_name
        self.target_dir = os.path.join(os.getcwd(), project_name)

    def __run__(self):
        base_dir = os.path.join(os.getcwd(), self.target_dir)
        print("全目录覆盖处理:", self.target_dir)
        try:
            for entry in os.listdir(base_dir):
                full_path = os.path.join(base_dir, entry)
                if os.path.isdir(full_path):
                    rel_path = os.path.relpath(full_path, os.getcwd())
                    print(rel_path)
                    Folder(rel_path).__run__()
        except FileNotFoundError:
            os.makedirs(base_dir, exist_ok=True)
            print(f"目录 {base_dir} 已自动创建")


class Folder:
    def __init__(self, rel_path):
        self.rel_path = rel_path
        self.abs_path = os.path.join(os.getcwd(), rel_path)
        self.folder_appeared_set = set()

    def __run__(self, cutoff_date='        ALL'):
        # EmailAddress: Dominik_For_Heybox@163.com
        # 前五个给这个邮箱发送邮件的学弟学妹有机会获得，请学长吃饭的机会:D  [doge]
        my_print1(f'{self.rel_path} from {cutoff_date} to now', 1)
        sorted_abs_part_subdir = get_sorted_abs_part_subdir(self.abs_path)
        for subdir in sorted_abs_part_subdir:
            Part(subdir, self.folder_appeared_set).__run__(
                cutoff_date)


class Part:

    def __init__(self, abs_path: str, folder_appeared_set):
        self.abs_path = abs_path
        self.current_count_dict = dict()
        self.used_dict = UsedDict().load()
        self.folder_appeared_set = folder_appeared_set

    def __run__(self, cutoff_date):
        if os.path.basename(self.abs_path)[:8] < cutoff_date:
            my_print2(f'{os.path.basename(self.abs_path)}:<{cutoff_date}', 1)
            self.read_new_md()
        else:
            my_print2(f'{os.path.basename(self.abs_path)}:>{cutoff_date}', 1)
            current_all_count_dict = self.get_current_all_count_dict()
            classified_and_gathered_dict = self.classify_and_gather_count_dict(current_all_count_dict)
            classified_and_gathered_new_dict, classified_and_gathered_old_dict = self.divide_new_and_old(
                classified_and_gathered_dict)
            md_new = self.dict_format_to_md(classified_and_gathered_new_dict)
            md_old = self.dict_format_to_md(classified_and_gathered_old_dict)
            self.save_md(md_new, Constants.New_)
            self.save_md(md_old, Constants.Old_)
        UsedDict().save(self.used_dict)

    def divide_new_and_old(self, current_all_count_dict):
        current_new_count_dict = dict()
        current_old_count_dict = dict()

        for key, value in current_all_count_dict.items():
            if key in self.folder_appeared_set:
                current_old_count_dict[key] = value
            else:
                current_new_count_dict[key] = value
                self.folder_appeared_set.add(key)
        my_print3(f'New words: {len(current_new_count_dict)}/Old words: {len(current_old_count_dict)}', 1)
        return current_new_count_dict, current_old_count_dict

    def classify_and_gather_count_dict(self, current_count_dict):
        classified_and_gathered_dict = dict()
        end = len(current_count_dict)
        cur = 0
        for key, value in current_count_dict.items():
            lemma = self.search_used_dict('classify', key)
            count_dict_add(classified_and_gathered_dict, lemma, value)
            cur += 1
            my_print3(f'-*classifying-({cur}/{end}){key}==>{lemma}')
        my_print3(f'-*classifying-done-({cur}/{end})', 1)
        return classified_and_gathered_dict

    def dict_format_to_md(self, classified_and_gathered_dict):
        structured_dict = self.structure_dict(classified_and_gathered_dict)
        md_content = []

        # 按指定顺序处理分类
        ordered_categories = sorted([cat for cat in structured_dict])
        for category in ordered_categories:
            words = structured_dict.get(category, list())
            display_name = category.upper()
            md_content.append(f'## {display_name}')

            for word in sorted(words, key=lambda x: x.count):
                line = f'- {word.__FORM__()}'
                md_content.append(line)

            md_content.append('')  # 添加空行分隔
        return '\n'.join(md_content).strip()

    def save_md(self, text, name):
        with open(os.path.join(self.abs_path, name), 'w', encoding='utf-8') as f:
            f.write(text)
        my_print3(f'--*saved_{os.path.join(self.abs_path, name)}', 1)

    def read_new_md(self):
        with open(os.path.join(self.abs_path, Constants.New_), 'r', encoding='utf-8') as f:
            words = extract_word_dict_from_docx(f.read())
            self.divide_new_and_old(words)
        my_print3(f'-*reading-done-({os.path.join(self.abs_path, Constants.New_)})', 1)

    def get_current_all_count_dict(self):
        current_all_count_dict = dict()
        for root, dirs, files in os.walk(self.abs_path):
            for file in files:
                if (file.lower().endswith('.md') and not file.endswith(Constants.New_) and not file.endswith(
                        Constants.Old_)) or file.lower().endswith('.pdf') or file.lower().endswith('.txt') or file.lower().endswith('.docx'):
                    file_path = os.path.join(root, file)
                    current_file_count_dict = extract_word_dict_from_docx(file_path)
                    my_print3(f'   --*reading_{len(current_file_count_dict)}_words_in_{file}', 1)
                    count_dict_add_dict(current_all_count_dict, current_file_count_dict)
        my_print3(f'--*reading_done_{len(current_all_count_dict)}_words_in_{self.abs_path}', 1)
        return current_all_count_dict

    def structure_dict(self, classified_and_gathered_dict):
        structured_dict = dict()
        end = len(classified_and_gathered_dict)
        cur = 0
        for key, value in classified_and_gathered_dict.items():
            lemma = self.search_used_dict('classify', key)
            upos = self.search_used_dict('upos', key)
            if upos == 'NOUN':
                lemma = lemma.capitalize()
            if upos not in structured_dict:
                structured_dict[upos] = list()
            chi = self.search_used_dict('translate', lemma)
            gen = self.search_used_dict('gender', lemma)
            structured_dict[upos].append(
                MdFormat(value, lemma, chi, gen))
            cur += 1
            my_print3(f'-*structuring-({cur}/{end}){lemma}==>{upos} {chi}')
        my_print3(f'-*structuring-done-({cur}/{end})', 1)
        return structured_dict

    def search_used_dict(self, group, key):
        if key in self.used_dict[group]:
            return self.used_dict[group][key]
        else:
            if group == 'classify' or group == 'upos':
                info = classify(key)
                self.used_dict['classify'][key] = info.lemma
                self.used_dict['upos'][key] = info.upos

            elif group == 'translate':
                self.used_dict[group][key] = translate_to_chi1(key)
            else:
                self.used_dict[group][key] = get_noun_gender(key)
            return self.used_dict[group][key]
