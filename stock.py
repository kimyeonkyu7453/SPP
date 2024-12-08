import pandas as pd
import requests
from io import StringIO

def get_stock_code():
    # 종목코드 다운로드
    url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download'
    response = requests.get(url)
    
    # 인코딩 설정: 한국 웹 페이지는 보통 euc-kr 인코딩을 사용
    response.encoding = 'euc-kr'
    
    # HTML 내용을 StringIO로 감싸서 pandas로 읽기
    stock_code = pd.read_html(StringIO(response.text), header=0)[0]
    
    # 필요한 열만 추출하고 컬럼명 변경
    stock_code = stock_code[['회사명', '종목코드']]
    stock_code = stock_code.rename(columns={'회사명': 'company', '종목코드': 'code'})
    
    # 종목코드 형식 맞추기: 6자리로
    stock_code.code = stock_code.code.map('{:06d}'.format)
    
    return stock_code

def get_stock(code):
    # 주식 데이터 수집 함수
    df = pd.DataFrame()
    for page in range(1, 21):  # 1~20 페이지의 데이터를 수집
        url = f'https://finance.naver.com/item/sise.naver?code={code}'
        url = f'{url}&page={page}'  # 페이지 추가

        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'}
        res = requests.get(url, headers=header)
        
        # HTML을 StringIO로 감싸서 pandas로 읽기
        try:
            current_df = pd.read_html(StringIO(res.text), header=0)[0]
            df = df._append(current_df, ignore_index=True)  # .append() 대신 ._append() 사용
        except ValueError as e:
            print(f"페이지 {page}에서 데이터를 가져올 수 없습니다: {e}")
            continue
    
    return df

def clean_data(df):
    # 데이터 전처리: 결측치 제거, 컬럼명 변경 및 타입 변환
    df = df.dropna()
    
    # 컬럼명 변경 (여기서 'colums' -> 'columns'로 수정)
    df = df.rename(columns={'날짜': 'date', '종가': 'close', '전일비': 'diff', '시가': 'open', '고가': 'high', '저가': 'low', '거래량': 'volume'})
    
    # 컬럼들이 제대로 변환되었는지 확인
    print("변경된 컬럼명:", df.columns)  # 디버깅을 위해 추가
    
    # 'close', 'diff', 'open', 'high', 'low', 'volume' 컬럼이 있는지 확인
    required_columns = ['close', 'diff', 'open', 'high', 'low', 'volume']
    for col in required_columns:
        if col not in df.columns:
            print(f"경고: '{col}' 컬럼이 없습니다.")
    
    # 열 데이터 타입 변환
    df[required_columns] = df[required_columns].astype(int)
    
    # 'date' 컬럼을 날짜 형식으로 변환
    df['date'] = pd.to_datetime(df['date'])
    
    # 날짜순으로 정렬
    df = df.sort_values(by=['date'], ascending=True)
    
    return df

# 종목명 설정 (예: 삼성전자)
company = '삼성전자'

# 종목코드 가져오기
stock_code = get_stock_code()

# 종목 코드 찾기
code = stock_code[stock_code.company == company].code.values[0].strip()

# 종목 데이터를 가져오기
df = get_stock(code)

# 데이터 전처리
df = clean_data(df)

# 결과 출력
print(df)
