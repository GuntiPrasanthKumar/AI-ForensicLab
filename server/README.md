# ⚙️ AI Forensic Lab — Backend API Specification

Express.js RESTful API service providing authentication, Turnstile CAPTCHA verification, and proxy routing to the Python AI Engine.

---

## 📡 Endpoints Overview

### 🔐 Authentication Routes (`/api/auth`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/auth/register` | Register new user & send 6-digit OTP | ❌ |
| `POST` | `/api/auth/verify-otp` | Verify 6-digit OTP email code | ❌ |
| `POST` | `/api/auth/resend-otp` | Resend 6-digit OTP email code | ❌ |
| `POST` | `/api/auth/login` | Authenticate user & set JWT cookie | ❌ |
| `GET` | `/api/auth/me` | Fetch active authenticated user profile | ✅ |
| `POST` | `/api/auth/logout` | Clear authentication session cookie | ✅ |

---

### 🔬 Detection Routes (`/api`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/detect` | Upload image/video file for AI analysis | ✅ |
| `POST` | `/api/detect-text` | Send raw text for perplexity/burstiness analysis | ✅ |
| `GET` | `/api/history` | Retrieve user's previous forensic scan results | ✅ |
| `DELETE`| `/api/history/:id` | Delete specific scan result | ✅ |

---

## 🛡️ Security Policies

- **Rate Limiting:** `authLimiter` limits authentication endpoints to 10 requests/hour.
- **NoSQL Injection:** `express-mongo-sanitize` scrubs query input selectors.
- **CSRF & Cookies:** `httpOnly`, `sameSite: lax`, `secure: true` on production.
