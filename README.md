# 🛡️ AI Forensic Lab

A multi-modal digital forensics platform designed to detect deepfakes, AI-generated synthetic images, and LLM-generated text with forensic precision.

---

## 🌟 Key Features

- 📹 **Deepfake Video Lab:** Tracks facial landmark aspect ratio stability across frames using OpenCV bounding-box variance analysis to detect temporal face-swap warping.
- 🖼️ **Image EXIF & Noise Lab:** Inspects physical camera hardware EXIF tags and structural noise patterns to identify Midjourney, DALL-E, and Stable Diffusion synthetic artifacts.
- 📝 **Linguistic Text Analysis:** Evaluates document perplexity, burstiness, information entropy, and sentence length variation to identify robotic AI writing.
- 🔑 **Secure Authentication:** Cookie-based session management, 6-digit OTP email verification, and Cloudflare Turnstile anti-bot protection.
- ⚡ **Local & Cloud Hybrid Engine:** High-performance local heuristic fallback engines combined with Gemini vision models.

---

## 🏗️ Architecture Overview

```
 ┌────────────────┐       ┌──────────────────────┐       ┌─────────────────────┐
 │ React Frontend │ <---> │  Node.js API Server  │ <---> │  Python AI Engine   │
 │   (Vite/Tailwind) │       │ (Express/MongoDB)    │       │ (FastAPI/OpenCV)    │
 └────────────────┘       └──────────────────────┘       └─────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites
- **Node.js** v18+
- **Python** 3.10+
- **MongoDB** (Local or Atlas instance)

### 1. Backend Setup
```bash
cd server
npm install
npm start
```

### 2. AI Engine Setup
```bash
cd ai-service
pip install -r requirements.txt
python main.py
```

### 3. Frontend Setup
```bash
cd client
npm install
npm run dev
```

---

## 🛡️ License

Distributed under the MIT License. See `LICENSE` for more information.
## System Architecture

```
Frontend (React + Vite) <---> Server (Express.js) <---> AI Service (PyTorch / ViT / TIMM)
```

## Environment Configuration

- `MONGO_URI`: MongoDB connection string
- `PORT`: Server port (default: 5000)
- `PRIMARY_IMAGE_MODEL`: Active image detection model key

## Local Development Setup

1. Install dependencies: `npm install` in client and server directories.
2. Run server: `npm run dev` inside server directory.
3. Run client: `npm run dev` inside client directory.
