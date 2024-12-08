const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const db = require('../../login-project/db'); // 데이터베이스 연결
require('dotenv').config(); // .env 파일에서 환경변수 불러오기

const router = express.Router();
const SECRET_KEY = process.env.SECRET_KEY || 'your_secret_key'; // JWT 서명 키 (환경 변수로 관리)

// 데이터베이스 쿼리의 비동기 처리를 위해 Promise 래핑
const queryAsync = (query, values) => {
    return new Promise((resolve, reject) => {
        db.query(query, values, (err, results) => {
            if (err) reject(err);
            resolve(results);
        });
    });
};

// 회원가입
router.post('/register', async (req, res) => {
    const { username, password, email } = req.body;

    // 데이터 유효성 검사
    if (!username || !password || !email) {
        return res.status(400).json({ message: 'Username, password, and email are required.' });
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        return res.status(400).json({ message: 'Invalid email format.' });
    }

    try {
        // 중복 사용자 확인
        const users = await queryAsync('SELECT * FROM users WHERE username = ? OR email = ?', [username, email]);

        if (users.length > 0) {
            return res.status(409).json({ message: 'Username or email already exists.' });
        }

        // 비밀번호 해시화 및 사용자 등록
        const hashedPassword = await bcrypt.hash(password, 10);
        await queryAsync('INSERT INTO users (username, password, email) VALUES (?, ?, ?)', [username, hashedPassword, email]);

        res.status(201).json({ message: 'User registered successfully!' });
    } catch (error) {
        console.error('Error during registration:', error);
        res.status(500).json({ message: 'Internal server error. Please try again later.' });
    }
});

// 로그인
router.post('/login', async (req, res) => {
    const { username, email, password } = req.body;

    // 데이터 유효성 검사
    if (!username && !email || !password) {
        return res.status(400).json({ message: 'Username or email and password are required.' });
    }

    try {
        // 사용자 조회: username 또는 email을 기준으로 조회
        const query = 'SELECT * FROM users WHERE username = ? OR email = ?';
        const users = await queryAsync(query, [username || email, username || email]);

        if (users.length === 0) {
            return res.status(404).json({ message: 'User not found.' });
        }

        const user = users[0];
        const isMatch = await bcrypt.compare(password, user.password);

        if (!isMatch) {
            return res.status(401).json({ message: 'Invalid credentials.' });
        }

        // JWT 토큰 생성
        const token = jwt.sign({ id: user.id, username: user.username }, SECRET_KEY, { expiresIn: '1h' });

        res.json({ message: 'Login successful!', token });
    } catch (error) {
        console.error('Error during login:', error);
        res.status(500).json({ message: 'Internal server error. Please try again later.' });
    }
});


module.exports = router;
