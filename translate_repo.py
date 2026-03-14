import os
import re
from deep_translator import GoogleTranslator

TARGET_LANG = 'en'
EXTENSIONS_TO_TRANSLATE = {'.sh', '.bat', '.py', '.md', '.txt', '.json', '.yml', '.yaml', '.html'}
TEXT_REPLACEMENTS = {
    "tesseract-ocr-chi-sim": "tesseract-ocr-eng",
    "tesseract-ocr-chi-tra": "",
    "chi_sim": "eng",
    "Chinese": "English",
    "chinese": "english",
}

def contains_chinese(text):
    return re.search(r'[\u3400-\u4dbf\u4e00-\u9fff]+', text) is not None

def get_indentation(line):
    match = re.match(r'^(\s*)', line)
    return match.group(1) if match else ""

def apply_keyword_replacements(text):
    for old, new in TEXT_REPLACEMENTS.items():
        text = text.replace(old, new)
    return text

def translate_block(text_block, indent):
    if not text_block.strip():
        return text_block
    try:
        lines_to_translate = [line.strip() for line in text_block.splitlines() if line.strip()]
        clean_text = "\n".join(lines_to_translate)
        translated = GoogleTranslator(source='auto', target=TARGET_LANG).translate(clean_text)
        if not translated: return text_block
        return "\n".join([f"{indent}{line}" for line in translated.splitlines()])
    except Exception:
        return text_block

def process_files():
    for root, dirs, files in os.walk("."):
        if '.git' in dirs: dirs.remove('.git')
        if '.github' in dirs: dirs.remove('.github')
            
        for file in files:
            if file == "translate_repo.py": continue
            if any(file.lower().endswith(ext) for ext in EXTENSIONS_TO_TRANSLATE):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    translated_lines = []
                    chinese_buffer = []
                    current_indent = ""

                    for line in lines:
                        if contains_chinese(line):
                            if not chinese_buffer: current_indent = get_indentation(line)
                            chinese_buffer.append(line)
                        else:
                            if chinese_buffer:
                                translated_lines.append(translate_block("".join(chinese_buffer), current_indent) + "\n")
                                chinese_buffer = []
                            translated_lines.append(line)
                    
                    if chinese_buffer:
                        translated_lines.append(translate_block("".join(chinese_buffer), current_indent) + "\n")

                    final_content = apply_keyword_replacements("".join(translated_lines))
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(final_content)
                except:
                    pass

if __name__ == "__main__":
    process_files()
