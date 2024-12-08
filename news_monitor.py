import requests
import time
from bs4 import BeautifulSoup

# 네이버 API 정보
client_id = "JKsHlQ0zDrONeViMDsq2"  # 네이버 개발자 센터에서 발급받은 ID
client_secret = "toBKlh0oX5"  # 네이버 개발자 센터에서 발급받은 Secret

# 네이버 뉴스 검색 함수
def search_naver_news(query, display=10, start=1, sort="date"):
    """
    네이버 뉴스 API를 사용하여 특정 키워드의 뉴스 검색 결과를 반환합니다.
    
    Parameters:
        - query (str): 검색할 키워드.
        - display (int): 가져올 뉴스 개수.
        - start (int): 검색 시작 위치.
        - sort (str): 정렬 순서, 'date'는 최신순.
    
    Returns:
        - dict: 뉴스 검색 결과 데이터.
    """
    url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display={display}&start={start}&sort={sort}"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error Code: {response.status_code}, Message: {response.content.decode()}")
        return None

# 기사 본문을 가져오는 함수
def get_article_content(link):
    """
    주어진 링크에서 뉴스 기사 본문을 가져옵니다.
    
    Parameters:
        - link (str): 뉴스 기사 URL.
    
    Returns:
        - str: 뉴스 기사 본문 텍스트. 본문을 가져오지 못한 경우 빈 문자열 반환.
    """
    try:
        response = requests.get(link)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # 본문 추출 예제 (언론사에 따라 구조가 다를 수 있음)
            content_div = soup.find('div', class_='article-content')  # 예시 클래스명
            if content_div:
                return content_div.get_text(strip=True)

            paragraphs = soup.find_all('p')  # 모든 <p> 태그 내용을 이어붙이기
            if paragraphs:
                return ' '.join([p.get_text(strip=True) for p in paragraphs])
        
        return ""  # 본문을 가져오지 못한 경우 빈 문자열 반환
    except Exception as e:
        print(f"기사 내용 가져오기 중 오류 발생: {e}")
        return ""

# 실시간으로 뉴스를 모니터링하는 함수
def monitor_news(query, interval=10):
    """
    지정된 간격마다 특정 키워드의 최신 뉴스를 모니터링합니다.
    
    Parameters:
        - query (str): 모니터링할 키워드.
        - interval (int): 뉴스 갱신 주기 (초 단위).
    """
    last_pub_date = None  # 마지막으로 출력된 뉴스의 발행 시간 저장

    while True:
        news_data = search_naver_news(query, display=5)

        if news_data and 'items' in news_data:
            new_news_found = False  # 새로운 뉴스 확인 여부

            for item in news_data['items']:
                pub_date = item['pubDate']  # 뉴스 발행 시간

                # 새로운 뉴스인지 확인
                if pub_date != last_pub_date:
                    new_news_found = True
                    print(f"Title: {item['title']}")
                    print(f"Link: {item['link']}")
                    print(f"Description: {item['description']}")
                    print(f"PubDate: {item['pubDate']}")

                    # 기사 본문 가져오기
                    article_content = get_article_content(item['link'])
                    if article_content:
                        print(f"Content: {article_content[:200]}...")  # 본문 일부만 출력
                    print("-" * 50)

                    # 가장 최근 뉴스 발행 시간 업데이트
                    last_pub_date = pub_date

            if not new_news_found:
                print("새로 올라온 뉴스가 없습니다.")

        else:
            print("뉴스 데이터가 없습니다.")

        time.sleep(interval)  # 지정된 간격으로 대기 후 다시 확인

# '삼성전자' 키워드로 실시간 뉴스 모니터링 시작 (10초마다 확인)
if __name__ == "__main__":
    monitor_news("삼성전자", interval=10)
