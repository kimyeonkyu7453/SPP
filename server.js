const express = require('express');
const cors = require('cors');
const authRoutes = require('./routes/auth'); // 인증 관련 API 처리
const db = require('./db'); // 데이터베이스 연결
const passport = require('passport');
const GoogleStrategy = require('passport-google-oauth20').Strategy;
const KakaoStrategy = require('passport-kakao').Strategy;
const session = require('express-session');
const bcrypt = require('bcryptjs');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// CORS 설정
app.use(cors({
    origin: process.env.FRONTEND_URL || 'http://localhost:3000', // 클라이언트 URL 설정
    methods: ['GET', 'POST'],
    allowedHeaders: ['Content-Type', 'Authorization'],
}));

// 세션 및 Passport 설정
app.use(session({
    secret: process.env.SESSION_SECRET || 'your_secret_key',
    resave: false,
    saveUninitialized: true,
}));

app.use(passport.initialize());
app.use(passport.session());

// JSON 형식의 요청 본문 처리
app.use(express.json());
app.use(express.static('public')); // 정적 파일 제공

// 인증 관련 API 라우트
app.use('/api/auth', authRoutes);

// Google OAuth 설정
passport.use(new GoogleStrategy({
    clientID: process.env.GOOGLE_CLIENT_ID,
    clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    callbackURL: `${process.env.BASE_URL}/auth/google/callback`,
  },
  function (token, tokenSecret, profile, done) {
    return done(null, profile); // Google 프로필 반환
  }
));

// Kakao OAuth 설정
passport.use(new KakaoStrategy({
    clientID: process.env.KAKAO_CLIENT_ID,
    clientSecret: process.env.KAKAO_CLIENT_SECRET,
    callbackURL: `${process.env.BASE_URL}/auth/kakao/callback`,
  },
  function (accessToken, refreshToken, profile, done) {
    return done(null, profile); // Kakao 프로필 반환
  }
));

// 세션에 사용자 정보를 저장
passport.serializeUser((user, done) => done(null, user));
passport.deserializeUser((id, done) => done(null, id));

// Google OAuth 라우트
app.get('/auth/google', passport.authenticate('google', { scope: ['profile', 'email'] }));

app.get('/auth/google/callback',
  passport.authenticate('google', { failureRedirect: '/login' }),
  (req, res) => {
    res.redirect('/home'); // 로그인 후 리디렉션
  }
);

// Kakao OAuth 라우트
app.get('/auth/kakao', passport.authenticate('kakao'));

app.get('/auth/kakao/callback',
  passport.authenticate('kakao', { failureRedirect: '/login' }),
  (req, res) => {
    res.redirect('/home'); // 로그인 후 리디렉션
  }
);

// 로그인 API 라우트 수정 (POST /api/auth/login)
app.post('/api/auth/login', (req, res) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return res.status(400).json({ message: 'Email and password are required' });
  }

  // 이메일로 사용자 조회
  const query = `SELECT * FROM users WHERE email = ?`;
  db.query(query, [email], (err, results) => {
    if (err) {
      return res.status(500).json({ message: 'Server error' });
    }

    if (results.length === 0) {
      return res.status(401).json({ message: 'Invalid credentials' });
    }

    const user = results[0];

    // 비밀번호 비교
    bcrypt.compare(password, user.password, (err, isMatch) => {
      if (err) {
        return res.status(500).json({ message: 'Server error' });
      }

      if (isMatch) {
        // 세션에 사용자 정보 저장
        req.session.user = { email: user.email, fullName: user.fullName, nickname: user.nickname };
        res.status(200).json({ message: 'Login successful', redirectTo: '/home' });
      } else {
        res.status(401).json({ message: 'Invalid credentials' });
      }
    });
  });
});

// 회원가입 API (닉네임 추가)
app.post('/api/auth/register', async (req, res) => {
  const { fullName, email, nickname, password } = req.body;

  if (!fullName || !email || !nickname || !password) {
    return res.status(400).json({ message: 'Full name, email, nickname, and password are required' });
  }

  const hashedPassword = await bcrypt.hash(password, 10);

  const query = `INSERT INTO users (fullName, email, nickname, password) VALUES (?, ?, ?, ?)`;
  db.query(query, [fullName, email, nickname, hashedPassword], (err, result) => {
    if (err) {
      return res.status(500).json({ message: 'Internal server error' });
    }
    res.status(201).json({ message: 'User registered successfully' });
  });
});

// 사용자 로그인 상태 확인 API
app.get('/api/auth/me', (req, res) => {
  if (req.session.user) {
    res.json(req.session.user);
  } else {
    res.status(401).json({ message: 'Not authenticated' });
  }
});

// 로그아웃 API
app.post('/logout', (req, res) => {
  req.session.destroy(err => {
    if (err) {
      return res.status(500).json({ message: 'Failed to log out' });
    }
    res.redirect('/login'); // 로그아웃 후 로그인 페이지로 리디렉션
  });
});

// 홈 페이지 라우트
app.get('/home', (req, res) => {
  if (req.session.user) {
    res.send(`Welcome, ${req.session.user.fullName}`);
  } else {
    res.redirect('/login');
  }
});

// 에러 핸들링
app.use((err, req, res, next) => {
  console.error('Error:', err.stack || err.message || err);
  res.status(err.status || 500).json({ message: err.message || 'Internal server error.' });
});

app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
