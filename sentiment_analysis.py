from transformers import pipeline

# 모델 로드
sentiment_analyzer = pipeline(
    "sentiment-analysis",
    model="nlp04/korean_sentiment_analysis_dataset3_best"  # 모델 ID
)

# 감성 분석 함수
def analyze_sentiment(news_text):
    if not news_text or len(news_text.strip()) == 0:
        return None, None  # 입력이 없거나 공백일 경우

    try:
        analysis = sentiment_analyzer(news_text)

        if len(analysis) > 0:
            # 레이블에 따라 긍정적 또는 부정적으로 변환
            label = analysis[0]['label']  # "positive", "negative", "neutral" 중 하나
            score = analysis[0]['score']  # 감성 점수 (확률)

            # 점수에 따라 감정 분류
            if score >= 0.6:
                sentiment = '긍정적'
            elif score >= 0.4:
                sentiment = '중립적'
            else:
                sentiment = '부정적'

            return sentiment, score  # 감정 유형과 점수 반환
        else:
            return None, None  # 분석할 내용이 없으면 None 반환
    except Exception as e:
        print(f"분석 중 오류 발생: {e}")
        return None, None  # 오류 발생 시 None 반환
