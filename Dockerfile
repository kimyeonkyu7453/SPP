# Node.js와 Python 환경을 설치한 이미지 사용
FROM node:22

# Python3 설치 (multi_flask.py를 실행하기 위해 필요)
RUN apt-get update && apt-get install -y python3 python3-pip

# 작업 디렉토리 설정
WORKDIR /app

# 프로젝트의 package.json과 package-lock.json을 복사하여 의존성 설치
COPY package.json package-lock.json ./
RUN npm install

# 애플리케이션의 모든 파일을 복사
COPY . .

# 애플리케이션이 실행될 포트 설정
EXPOSE 3000

# `npm run dev`를 실행하여 Node.js 서버와 Python Flask 서버를 동시에 실행
# CMD 명령어를 sh 쉘을 통해 실행하도록 수정
CMD ["sh", "-c", "npm run dev"]
