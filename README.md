# 🚀 ApplixyBot

ApplixyBot is an AI-powered personal career agent that lives exclusively inside Telegram. It automatically finds remote and relevant tech jobs across multiple boards, analyzes your resume against job descriptions using cutting-edge ATS matching, and instantly engineers hyper-tailored cover letters that boost your application success rates. 

## ✨ Key Features
- **🌍 Multi-Source Tech Job Scraper:** Pulls jobs from Indeed, WeWorkRemotely, Remotive, Arbeitnow, and Jobicy, then normalizes them directly into your workflow. Automatically filters out irrelevant roles according to `Job_titles.txt`.
- **🧠 Local Setup AI Resume Analyzer:** Validates your skills against actual job descriptions and heavily penalizes experience/core domain mismatches to give you realistic match scores.
- **✍️ Hyper-Tailored Cover Letters:** Using NVIDIA NIM APIs (Llama3-70B), the bot generates punchy, 150-word cover letters built specially for each job.
- **📊 Job Tracker & Stats:** Integrated "My Applications" dashboard lets you track where you applied and review your weekly submission summaries to stay productive.
- **💎 Monetization:** Fully baked Free and Pro subscription tiers. Connects directly to Razorpay with instant webhook activations. 

## 🏗 Tech Stack
- **Frameworks:** Python 3.12, `python-telegram-bot` (v21+), FastAPI, APScheduler
- **Database:** Supabase (PostgreSQL), manipulated via `asyncpg`
- **AI Backend:** NVIDIA NIM API (Meta Llama 3 70B & 8B)
- **Deployment Strategy:** Uvicorn + Playwright, perfectly optimized for $0 PaaS hosting (like Railway.app) 

## 🛠 Self-Hosting & Deployment

We strongly recommend hosting on **Railway** paired with a free **Supabase** database for a 100% $0 running cost. 

### 1. Database Setup
1. Create a free project on Supabase.
2. Under "SQL Editor", run the commands in `db/schema.sql`.
3. Go to your Database settings and copy your **Transaction Connection String** (`postgres://...`).

### 2. Run Locally
```bash
# Clone the repo
git clone https://github.com/shubham-writes/ApplixyBot.git
cd ApplixyBot

# Setup venv
python -m venv venv
venv\Scripts\activate # On Windows

# Install dependencies  
pip install -r requirements.txt
playwright install chromium

# Create a .env file based on config.py (you will need your TELEGRAM_BOT_TOKEN)
# Run the Bot:
python main.py
```

### 3. Deploy to Railway ($0 hosting route)
1. Fork or push this repository to your GitHub account.
2. Sign into [Railway.app](https://railway.app), click **New Project** -> **Deploy from GitHub repo**.
3. In your Railway service **Variables** section, populate all required variables (see `.env_example`). 
4. **CRITICAL SETTINGS:** Set the following explicit Railway variables:
   - `ENVIRONMENT=production`
   - `WEBHOOK_URL=https://your-custom-railway-domain.up.railway.app`
5. The App will automatically configure its own webhooks dynamically. Grab some ☕️ while `railway.json` takes care of the Chromium and Uvicorn deployment instructions!

---

*Made with ❤️ by Shubham*
