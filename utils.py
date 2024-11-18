# 유틸리티 함수 및 번역 관련 모듈
import re
import deepl
import os
from dotenv import load_dotenv

# 환경 변수 로드 및 DeepL API 설정
load_dotenv()
DEEPL_API_KEY = os.getenv("DEEPL_API_KEY")
translator = deepl.Translator(DEEPL_API_KEY)

# 텍스트 번역
# - DeepL API
async def translate_text_deepl(text, target_lang='KO'):
    try:
        result = translator.translate_text(text, target_lang=target_lang)
        return result.text
    except Exception as e:
        print(f"[ERROR] DeepL 오류: {e}")
        return text

# 메시지가 중국어인지 확인
def is_message_chinese(message_content):
    chinese_numeric_regex = re.compile(r"[\u4E00-\u9FFF]")
    total_characters = len(message_content.replace(" ", ""))
    if total_characters == 0:
        return False
    chinese_numeric_count = len(chinese_numeric_regex.findall(message_content))
    return (chinese_numeric_count / total_characters) >= 0.6

# 메시지가 한국어가 아닌지
def is_not_korean(message_content):
    # 메시지가 :로 시작하고 :로 끝나는 경우(이모티콘) 제외
    if message_content.startswith("<") and message_content.endswith(">"):
        return False  # 조건에 해당하면 False 반환
    
    # 한글 유니코드 범위 정규식
    korean_regex = re.compile(r"[\uAC00-\uD7A3\u1100-\u11FF\u3131-\u318E]")
    # 남겨야 할 문자 정규식: 모든 언어(한국어, 영어, 중국어, 일본어 등)
    allowed_char_regex = re.compile(r"[^\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7A3\u1100-\u11FF\u3131-\u318Ea-zA-Z]")

    # 제외 대상 필터링: 공백, 숫자, 특수문자 등 제거
    filtered_content = allowed_char_regex.sub("", message_content)

    # 공백 제거 후 남은 문자 수
    total_characters = len(filtered_content)
    if total_characters == 0:
        return False  # 유효한 텍스트가 없으면 False 반환

    # 한국어 문자의 개수 계산
    korean_count = len(korean_regex.findall(filtered_content))
    
    # 한국어 비율 계산 및 30% 미만인지 확인
    return (korean_count / total_characters) < 0.3

# 공유된 텍스트를 인용 형식으로 변환
def format_as_quote(text):
    # 텍스트를 줄바꿈(`\n`)을 기준으로 분리한 후, 각 줄 앞에 `>` 추가
    return '\n'.join([f"> {line}" for line in text.splitlines()])