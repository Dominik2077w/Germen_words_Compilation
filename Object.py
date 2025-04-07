import os
import warnings

from Methode import classify, count_dict_add, get_sorted_abs_part_subdir, Constants, count_dict_add_dict, \
    extract_word_dict_from_docx, translate_to_chi, MdFormat, get_noun_gender, my_print1, my_print2, my_print3

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
        self.history_count_dict = dict()
        self.used_dict_for_classify = dict()
        self.used_dict_for_translate = dict()
        self.used_dict_for_gender = dict()

    def __run__(self, cutoff_date='        ALL'):
        #EmailAddress: Dominik_For_Heybox@163.com
        #前五个给这个邮箱发送邮件的学弟学妹有机会获得，请学长吃饭的机会:D  [doge]
        my_print1(f'{self.rel_path} from {cutoff_date} to now', 1)
        sorted_abs_part_subdir = get_sorted_abs_part_subdir(self.abs_path)
        for subdir in sorted_abs_part_subdir:
            Part(subdir, self.history_count_dict, self.used_dict_for_classify, self.used_dict_for_translate,
                 self.used_dict_for_gender).__run__(
                cutoff_date)


class Part:

    def __init__(self, abs_path: str, history_count_dict, used_dict_for_classify, used_dict_for_translate,
                 used_dict_for_gender):
        self.used_dict_for_gender = used_dict_for_gender
        self.abs_path = abs_path
        self.history_count_dict = history_count_dict
        self.current_count_dict = dict()
        self.used_dict_for_classify = used_dict_for_classify
        self.used_dict_for_translate = used_dict_for_translate

    def __run__(self, cutoff_date):
        if os.path.basename(self.abs_path)[:8] < cutoff_date:
            my_print2(f'{os.path.basename(self.abs_path)}:<{cutoff_date}', 1)
            self.read_new_md()
        else:
            my_print2(f'{os.path.basename(self.abs_path)}:>{cutoff_date}', 1)
            current_all_count_dict = self.get_current_all_count_dict()
            current_new_count_dict, current_old_count_dict = self.divide_new_and_old(current_all_count_dict)
            classified_and_gathered_new_dict = self.classify_and_gather_count_dict(current_new_count_dict)
            classified_and_gathered_old_dict = self.classify_and_gather_count_dict(current_old_count_dict)
            md_new = self.dict_format_to_md(classified_and_gathered_new_dict)
            md_old = self.dict_format_to_md(classified_and_gathered_old_dict)
            self.save_md(md_new, Constants.New_)
            self.save_md(md_old, Constants.Old_)

    def divide_new_and_old(self, current_all_count_dict):
        current_new_count_dict = dict()
        current_old_count_dict = dict()

        for key, value in current_all_count_dict.items():
            if key in self.used_dict_for_classify:
                current_old_count_dict[key] = value
            else:
                current_new_count_dict[key] = value
        my_print3(f'New words: {len(current_new_count_dict)}/Old words: {len(current_old_count_dict)}', 1)
        return current_new_count_dict, current_old_count_dict

    def classify_and_gather_count_dict(self, current_count_dict):
        classified_and_gathered_dict = dict()
        end = len(current_count_dict)
        cur = 0
        for key, value in current_count_dict.items():
            info = self.get_or_add_used_dict_for_classify(key)
            count_dict_add(classified_and_gathered_dict, info.lemma, value)
            cur += 1
            my_print3(f'-*classifying-({cur}/{end}){key}==>{info.lemma}')
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

    def get_or_add_used_dict_for_classify(self, key):
        if key in self.used_dict_for_classify:
            return self.used_dict_for_classify[key]
        else:
            info = classify(key)
            self.used_dict_for_classify[key] = info
            return info

    def load_used_dict_for_classify(self, key):
        self.used_dict_for_classify[key] = classify(key)

    def get_or_add_used_dict_for_gender(self, key):
        if key in self.used_dict_for_gender:
            return self.used_dict_for_gender[key]
        else:
            gen = get_noun_gender(key)
            self.used_dict_for_gender[key] = gen
            return gen

    def load_used_dict_for_gender(self, key, value):
        self.used_dict_for_gender[key] = value

    def get_or_add_used_dict_for_translate(self, key):
        if key in self.used_dict_for_translate:
            return self.used_dict_for_translate[key]
        else:
            # 这里可以添加翻译逻辑
            translated = translate_to_chi(key)
            self.used_dict_for_translate[key] = translated
            return translated

    def load_used_dict_for_translate(self, key, value):
        self.used_dict_for_translate[key] = value

    def save_md(self, text, name):
        with open(os.path.join(self.abs_path, name), 'w', encoding='utf-8') as f:
            f.write(text)
        my_print3(f'--*saved_{os.path.join(self.abs_path, name)}', 1)

    def read_new_md(self):
        with open(os.path.join(self.abs_path, Constants.New_), 'r', encoding='utf-8') as f:
            lines = f.readlines()
            end = len(lines)
            cur = 0
            for line in lines:
                if line.startswith('-'):
                    line = line[2:].replace('\n', '')
                    words = line.split(" ")
                    if len(words) < 4:
                        self.load_used_dict_for_classify(words[-2])
                        self.load_used_dict_for_translate(words[-2], words[-1])
                        cur += 1
                        my_print3(f'-*reading-({cur}/{end}){line}')
                    else:
                        self.load_used_dict_for_classify(words[-2])
                        self.load_used_dict_for_translate(words[-2], words[-1])
                        self.load_used_dict_for_gender(words[-2], words[-3])
                        cur += 1
                        my_print3(f'-*reading-({cur}/{end}){line}')
        my_print3(f'-*reading-done-({cur}/{end})', 1)

    def get_current_all_count_dict(self):
        current_all_count_dict = dict()
        for root, dirs, files in os.walk(self.abs_path):
            for file in files:
                if (file.lower().endswith('.md') and not file.endswith(Constants.New_) and not file.endswith(
                        Constants.Old_)) or file.lower().endswith('.pdf'):
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
            info = self.get_or_add_used_dict_for_classify(key)
            if info.upos == 'NOUN':
                info.lemma = info.lemma.capitalize()
            if info.upos not in structured_dict:
                structured_dict[info.upos] = list()
            chi = self.get_or_add_used_dict_for_translate(info.lemma)
            gen = self.get_or_add_used_dict_for_gender(info.lemma)
            structured_dict[info.upos].append(
                MdFormat(value, info.lemma, chi, gen))
            cur += 1
            my_print3(f'-*structuring-({cur}/{end}){info.lemma}==>{info.upos} {chi}')
        my_print3(f'-*structuring-done-({cur}/{end})', 1)
        return structured_dict
