FROM python:3.10-slim

RUN apt-get update && apt-get install -y curl git && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs

# Python 버전 확인
RUN python --version

# pip 최신화
RUN pip install --upgrade pip

# 작업 디렉토리 설정
WORKDIR /app

# Node.js 의존성 설치
COPY package.json package-lock.json ./
RUN npm install

# Python 의존성 설치
COPY requirements.txt ./
RUN pip install -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# 실행 포트 노출
EXPOSE 3000

# Node.js와 Python Flask 동시 실행
RUN npm install -g concurrently
CMD ["concurrently", "\"npm start\"", "\"python3 multi_flask.py\""]
