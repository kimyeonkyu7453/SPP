# Python과 Node.js 환경이 포함된 기본 이미지 사용
FROM python:3.10-slim

# Node.js 설치 (Node.js 22 버전 사용)
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs

# 작업 디렉토리 설정
WORKDIR /app

# Node.js 의존성 설치
COPY package.json package-lock.json ./
RUN npm install

# Python 의존성 설치
COPY requirements.txt ./
RUN pip install -r requirements.txt

# 애플리케이션의 모든 파일 복사
COPY . .

# 애플리케이션 실행 포트 노출
EXPOSE 3000

# Python Flask와 Node.js 서버를 동시에 실행하기 위해 concurrently 설치
RUN npm install -g concurrently

# Node.js와 Python 서버를 동시에 실행
CMD ["concurrently", "\"npm start\"", "\"python3 multi_flask.py\""]
