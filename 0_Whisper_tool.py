import whisper
import json
import os
import re


def transcribe_audio(wav_path):
    # 加载模型
    model = whisper.load_model("medium", device="cpu")

    # 转录音频文件，指定德语
    result = model.transcribe(wav_path, language="de", fp16=False,verbose=True, no_speech_threshold=2)

    # 构造JSON文件路径
    json_path = os.path.splitext(wav_path)[0] + '.json'

    # 新增时间格式转换函数
    def convert_time(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"

    # 生成txt文件内容
    txt_content = []
    for segment in result['segments']:
        start_time = convert_time(segment['start'])
        end_time = convert_time(segment['end'])
        txt_line = f"[{start_time} --> {end_time}] {segment['text'].strip()}"
        txt_content.append(txt_line)

    # 保存txt文件
    txt_path = os.path.splitext(wav_path)[0] + '.md'
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(txt_content))
    return txt_path
if __name__ == '__main__':
    # 示例用法
    wav_path = "Data/PM/20250328_Speache/2025年03月28日 下午12点46分.m4a..mp3"  # 替换为你的音频文件路径
    json_path = transcribe_audio(wav_path)