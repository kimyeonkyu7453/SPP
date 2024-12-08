const mysql = require('mysql2');
require('dotenv').config(); // 환경 변수 사용을 위한 dotenv 추가

// 데이터베이스 연결 풀 설정
const connectionPool = mysql.createPool({
    host: process.env.DB_HOST || 'localhost',
    user: process.env.DB_USER || 'root',
    password: process.env.DB_PASSWORD || '11140255', // 환경 변수로 처리 가능
    database: process.env.DB_NAME || 'login_db',
    waitForConnections: true, // 연결이 다 차면 대기하도록 설정
    connectionLimit: 10, // 연결 풀 크기 설정
    queueLimit: 0, // 대기열의 크기 제한
});

// 프로미스를 반환하는 쿼리 실행 함수 (async/await 사용을 위한)
const query = (sql, params) => {
    return new Promise((resolve, reject) => {
        connectionPool.query(sql, params, (err, results) => {
            if (err) {
                console.error('Database query error:', err); // 에러 로그 추가
                reject(err); // 에러 발생 시 reject
            } else {
                resolve(results); // 성공 시 결과 반환
            }
        });
    });
};

// 예시: 데이터베이스 연결 상태 확인 함수
connectionPool.getConnection((err, connection) => {
    if (err) {
        console.error('Error connecting to the database:', err);
        process.exit(1); // 연결 실패 시 프로세스 종료
    } else {
        console.log('Connected to the MySQL database.');
        connection.release(); // 연결을 반환하여 풀에서 재사용할 수 있도록 함
    }
});

module.exports = { query, connectionPool };
