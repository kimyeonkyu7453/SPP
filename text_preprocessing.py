import re
from konlpy.tag import Okt

okt = Okt()  # Okt 객체 생성

# HTML 태그 및 특수 문자 제거 (숫자와 주식 관련 특수 문자는 유지)
def clean_text(text):
    text = re.sub(r'<[^>]+>', '', text)  # HTML 태그 제거
    # 숫자와 특수 문자 (%, ₩, $, 등) 유지, 나머지 불필요한 문자는 제거
    text = re.sub(r'[^가-힣a-zA-Z0-9\s%\.\,\$\₩]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()  # 여분의 공백 제거
    return text

# 불용어 제거 (필요하다면 수정)
korean_stopwords = ['그리고', '하지만', '이것', '그것', '저것']

def remove_stopwords(text):
    tokens = text.split()
    tokens = [word for word in tokens if word not in korean_stopwords]
    return ' '.join(tokens)

# 어간 추출 (형태소 분석)
def lemmatize(text):
    tokens = okt.pos(text, stem=True)  # Okt를 사용하여 형태소 분석
    return ' '.join([word for word, pos in tokens])

# 전처리 파이프라인
def preprocess_news(text):
    text = clean_text(text)
    text = remove_stopwords(text)
    text = lemmatize(text)
    return text
