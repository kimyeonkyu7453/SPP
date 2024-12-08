import asyncio
from news_monitor import search_naver_news, get_article_content  # 뉴스 검색 및 본문 가져오기 함수
from text_preprocessing import preprocess_news, clean_text  # 전처리 함수
from sentiment_analysis import analyze_sentiment  # 감성 분석 함수

# 주식 관련 키워드 리스트
stock_keywords = ["삼성전자", "하이닉스", "네이버", "현대차", "셀트리온", "주가", "주식", "매도", "매수", "개미", "증시", "상승", "하락"]

# 주식 관련 문장만 추출하는 함수
def extract_stock_related_sentences(text, keywords):
    sentences = text.split('.')  # 문장을 마침표 기준으로 분리
    stock_related_sentences = [sentence for sentence in sentences if any(keyword in sentence for keyword in keywords)]
    return '. '.join(stock_related_sentences)  # 주식 관련 문장들만 연결하여 반환

# 실시간 뉴스 모니터링 및 감성 분석
async def monitor_news_with_preprocessing_and_sentiment(keyword, interval=10):
    last_pub_date = None
    last_titles = set()  # 이전에 본 뉴스 제목들을 저장하는 집합

    while True:
        try:
            # 네이버 뉴스 검색
            news_data = search_naver_news(keyword, display=5)

            if news_data and 'items' in news_data:
                new_news_found = False

                for item in news_data['items']:
                    pub_date = item.get('pubDate')
                    title = item.get('title', '').strip()  # 뉴스 제목

                    # 새로운 뉴스 제목일 경우에만 감성 분석 수행
                    if title not in last_titles:
                        new_news_found = True
                        last_titles.add(title)  # 새로운 뉴스 제목 추가

                        # 뉴스 제목과 설명을 가져옴
                        news_text = f"{item.get('title', '')} {item.get('description', '')}"

                        # HTML 태그 제거
                        news_text = clean_text(news_text)

                        # 뉴스 기사 본문 가져오기
                        article_content = get_article_content(item.get('link', ''))

                        # 기사 본문이 있다면 제목과 설명에 본문을 추가
                        if article_content:
                            article_content = clean_text(article_content)  # 본문도 HTML 태그 제거
                            news_text += f" {article_content}"

                        # 주식 관련 키워드를 포함한 문장만 추출
                        stock_related_text = extract_stock_related_sentences(news_text, stock_keywords)

                        if stock_related_text:  # 주식 관련 문장이 있을 때만 감성 분석 수행
                            # 전처리 및 감성 분석
                            preprocessed_text = preprocess_news(stock_related_text)
                            
                            # 감성 분석 결과
                            sentiment, score = analyze_sentiment(preprocessed_text)

                            # 점수에 따라 감정 분류
                            if score >= 0.6:
                                sentiment_label = "긍정적"
                            elif score >= 0.4:
                                sentiment_label = "중립적"
                            else:
                                sentiment_label = "부정적"

                            # 분석에 사용된 텍스트와 결과 출력
                            print("--------------------------------------------------")
                            print(f"Keyword: {keyword}")
                            print(f"Title: {item.get('title', '제목 없음')}")
                            print(f"Link: {item.get('link', '링크 없음')}")
                            print(f"Description: {item.get('description', '설명 없음')}")
                            print(f"Sentiment: {sentiment_label}, Score: {score:.2f}")
                            print(f"PubDate: {item.get('pubDate', '발행일 없음')}")
                            print(f"Analyzed Stock-Related Text: {preprocessed_text}")  # 감성 분석에 사용된 텍스트 출력
                            print("--------------------------------------------------")
                        else:
                            print(f"Title: {item.get('title', '제목 없음')} - 주식 관련 문장이 없어 분석을 건너뜁니다.")

                        last_pub_date = pub_date

                if not new_news_found:
                    print(f"새로 올라온 뉴스가 없습니다 ({keyword}).")
            else:
                print(f"뉴스 데이터가 없습니다 ({keyword}).")
        
        except Exception as e:
            print(f"오류 발생: {e}")

        # 비동기 대기
        await asyncio.sleep(interval)

# 여러 키워드에 대해 실시간 뉴스 모니터링 시작
async def monitor_multiple_keywords(keywords, interval=10):
    tasks = [monitor_news_with_preprocessing_and_sentiment(keyword, interval) for keyword in keywords]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    # 주식 관련 5개 키워드로 뉴스 모니터링 시작
    asyncio.run(monitor_multiple_keywords(["삼성전자", "하이닉스", "네이버", "현대차", "셀트리온"], interval=10))
