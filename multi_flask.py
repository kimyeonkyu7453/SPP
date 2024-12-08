from flask import Flask, render_template, jsonify
import asyncio
from news_monitor import search_naver_news, get_article_content
from text_preprocessing import preprocess_news, clean_text
from sentiment_analysis import analyze_sentiment
from flask_cors import CORS

app = Flask(__name__)

# CORS 설정: 모든 도메인에서의 접근을 허용 (모바일 앱도 포함)
CORS(app, resources={r"/*": {"origins": "*"}})

# 주식 관련 키워드 리스트
stock_keywords = ["삼성전자", "sk하이닉스", "네이버", "현대차", "셀트리온"]

# 뉴스 데이터를 저장할 전역 변수
news_results = []

# 주식 관련 문장 추출 함수
def extract_stock_related_sentences(text, keywords):
    relevant_sentences = []
    sentences = text.split('. ')
    for sentence in sentences:
        for keyword in keywords:
            if keyword in sentence:
                relevant_sentences.append(sentence)
                break
    return ' '.join(relevant_sentences)

# 뉴스 모니터링 함수
async def monitor_news_with_preprocessing(keywords):
    global news_results
    tasks = []
    for keyword in keywords:
        tasks.append(fetch_and_analyze_news(keyword))
    await asyncio.gather(*tasks)

# 개별 키워드에 대해 뉴스 가져오고 분석하는 비동기 함수
async def fetch_and_analyze_news(keyword):
    global news_results
    news_data = search_naver_news(keyword, display=5)
    if news_data and 'items' in news_data:
        for item in news_data['items']:
            title = item.get('title', '').strip()
            link = item.get('link', '')
            description = clean_text(item.get('description', ''))
            pub_date = item.get('pubDate', '')

            article_content = get_article_content(link)
            if article_content:
                article_content = clean_text(article_content)
                news_text = f"{description} {article_content}"
                stock_related_text = extract_stock_related_sentences(news_text, stock_keywords)

                if stock_related_text:
                    preprocessed_text = preprocess_news(stock_related_text)
                    sentiment, score = analyze_sentiment(preprocessed_text)

                    # score가 None일 경우 처리 추가
                    if score is None:
                        sentiment_label = "중립"
                        score = 0.5  # 예시로 score를 0.5로 설정
                    else:
                        sentiment_label = "긍정" if score >= 0.6 else "중립" if score >= 0.4 else "부정"

                    news_results.append({
                        "keyword": keyword,
                        "title": title,
                        "link": link,
                        "description": description,
                        "sentiment": sentiment_label,
                        "score": f"{score:.2f}",
                        "pub_date": pub_date,
                        "analyzed_text": preprocessed_text
                    })

# 비동기 작업을 Flask에서 실행하는 방법
@app.route('/start-monitoring', methods=['POST'])
def start_monitoring():
    # 비동기 함수 실행을 위한 새 이벤트 루프 생성
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(monitor_news_with_preprocessing(stock_keywords))
    return jsonify({"status": "Monitoring started!"})

@app.route('/get-news', methods=['GET'])
def get_news():
    return jsonify(news_results)

@app.route('/')
def index():
    return render_template('news.html', news_results=news_results)

if __name__ == '__main__':
    # Flask 서버를 외부에서 접근할 수 있도록 0.0.0.0으로 설정
    app.run(debug=True, host='0.0.0.0', port=5000)
