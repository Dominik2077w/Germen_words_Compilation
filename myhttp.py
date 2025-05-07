import logging
import time
from datetime import datetime
from typing import List, Any, Callable

import requests

session = requests.Session()
from tools import *


class DeepSeekCache:
    def __init__(self):
        self.used_dict = {}
        self.load_cache()

    def load_cache(self):
        try:
            with open(Constants.DEEPSEEK_CACHE_PATH, 'r', encoding='utf-8') as f:
                self.used_dict = json.load(f)
        except FileNotFoundError:
            self.used_dict = {}
        except json.JSONDecodeError:
            self.used_dict = {}
            print(f"错误：缓存文件 {Constants.DEEPSEEK_CACHE_PATH} 格式错误，已重置为默认值")

    def save_cache(self):
        with open(Constants.DEEPSEEK_CACHE_PATH, 'w', encoding='utf-8') as f:
            json_code = json.dumps(self.used_dict, ensure_ascii=False, indent=4)
            f.write(json_code)

    def set_cache(self, key, value):
        self.used_dict[key] = value

    def get_cache(self, key):
        if key in list(self.used_dict.keys()):
            return self.used_dict[key]
        else:
            return None


deepSeekCache = DeepSeekCache()


def get_request_type(prompt: str) -> str:
    if prompt == Constants.PromptForNotizen:
        return "Notizen"
    elif prompt == Constants.PromptForFormat:
        return "Format"
    else:
        return "未知请求类型"


def get_formatted_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ask_deepseek(prompt: str, text: str, status: str) -> str:
    content = prompt + text
    global deepSeekCache
    value = deepSeekCache.get_cache(prompt + text)
    if value:
        print(
            f"{get_formatted_timestamp()} 内存缓存命中: {get_request_type(prompt)} {status} {text.replace(chr(10), ' ')}")
        return value
    # 检查内存缓存

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {Constants.DEEPSEEK_API_KEY}"
    }

    request_data = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": content}],
        "stream": False
    }
    try:
        print(
            f"{get_formatted_timestamp()} 新网络请求: {get_request_type(prompt)} {status} {text.replace(chr(10), ' ')}")

        # 使用缓存会话发送请求
        global session
        response = session.post(url, json=request_data, headers=headers)

        if response.status_code == 200:
            response_data = json.loads(response.text)
            if response_data.get("choices") and len(response_data["choices"]) > 0:
                ans = response_data["choices"][0]["message"]["content"]
                print(
                    f"{get_formatted_timestamp()} 回复接收 {get_request_type(prompt)} {status} {ans.replace(chr(10), ' ')}")
                deepSeekCache.set_cache(prompt + text, ans)
                return ans

        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", "60"))
            logging.info(f"{get_formatted_timestamp()} 请求过于频繁 429 {status} {text.replace(chr(10), ' ')}")
            time.sleep(retry_after)
            return ask_deepseek(prompt, text, status)

        else:
            error_msg = response.text if response.text else f"请求失败，状态码: {response.status_code}"
            logging.error(f"{get_formatted_timestamp()} {error_msg} {status} {text.replace(chr(10), ' ')}")

    except Exception as e:
        logging.fatal(f"{get_formatted_timestamp()} 请求异常: {str(e)} {status} {text.replace(chr(10), ' ')}")

    return ask_deepseek(prompt, text, status)


def process_array(array: List[Any], func: Callable) -> List[Any]:
    global deepSeekCache
    results = [None] * len(array)  # 预分配结果列表
    total = len(array)
    semaphore = threading.Semaphore(20)  # 使用信号量控制并发数
    threads = []

    def worker(item: Any, index: int):
        """线程工作函数"""
        with semaphore:  # 获取信号量
            try:
                results[index] = func(item, f'"{index + 1}/{total}"')
            except Exception as e:
                print(f"处理异常: {e}")

    # 创建所有线程
    for i, item in enumerate(array):
        thread = threading.Thread(target=worker, args=(item, i))
        threads.append(thread)
        thread.start()
        time.sleep(0.1)  # 保持原有的延迟逻辑

    # 等待所有线程完成
    for thread in threads:
        thread.join()
    deepSeekCache.save_cache()

    return results
