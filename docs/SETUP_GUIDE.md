# Koi Developer Setup Guide

Complete walkthrough for setting up the Koi development environment on macOS.

---

## Prerequisites

Before starting, make sure you have the following installed:

| Tool | Version | Check Command | Install |
|------|---------|---------------|---------|
| **Node.js** | 18+ | `node --version` | `brew install node` |
| **Python** | 3.11+ | `python3 --version` | `brew install python@3.11` |
| **Poetry** | Latest | `poetry --version` | `curl -sSL https://install.python-poetry.org \| python3 -` |
| **Expo CLI** | Latest | `npx expo --version` | `npm install -g expo-cli` |
| **Git** | Latest | `git --version` | `brew install git` |
| **Homebrew** | Latest | `brew --version` | [brew.sh](https://brew.sh) |

---

## 1. Clone the Repository

```bash
cd ~/
git clone git@gitlab.com:YOUR_USERNAME/koi-app.git
cd koi-app
```

---

## 2. Create External Accounts

You need four external service accounts. Create them in this order:

### 2.1 Sarvam AI
1. Go to [sarvam.ai](https://www.sarvam.ai)
2. Sign up for a developer account
3. Navigate to the API section
4. Generate an API key
5. Save it -- you will need it for the `.env` file

### 2.2 LiveKit Cloud
1. Go to [cloud.livekit.io](https://cloud.livekit.io)
2. Create a new project (name: "koi")
3. From the project dashboard, copy:
   - **API Key**
   - **API Secret**
   - **WebSocket URL** (looks like `wss://your-project.livekit.cloud`)

### 2.3 Supabase
1. Go to [supabase.com](https://supabase.com)
2. Create a new project:
   - **Name:** koi
   - **Region:** South Asia (Mumbai) -- important for latency
   - **Password:** Generate a strong password and save it
3. Once the project is ready, go to **Settings > API** and copy:
   - **Project URL** (the `SUPABASE_URL`)
   - **anon/public key** (the `SUPABASE_ANON_KEY`)
   - **service_role key** (the `SUPABASE_SERVICE_KEY`)
4. Go to **Settings > Database** and copy:
   - **Connection string** (the `SUPABASE_DB_URL` -- use the one for "Direct connection")

### 2.4 Pinecone
1. Go to [pinecone.io](https://www.pinecone.io)
2. Create a free account
3. Create a new index:
   - **Name:** `koi-memories`
   - **Dimensions:** `1024`
   - **Metric:** `cosine`
   - **Cloud:** AWS, region closest to India
4. Copy your **API key** from the dashboard

---

## 3. Environment Setup

### 3.1 Create the `.env` file

```bash
cp .env.example .env
```

If `.env.example` does not exist, create `.env` in the project root:

```bash
# ~/koi-app/.env

# Sarvam AI
SARVAM_API_KEY=your_sarvam_key_here

# LiveKit
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=wss://your-project.livekit.cloud

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key
SUPABASE_DB_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# Pinecone
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX=koi-memories
```

### 3.2 Set up Supabase Database

Run the database migrations. Go to **Supabase Dashboard > SQL Editor** and execute the migration files found in `supabase/migrations/` in numerical order:

```
001_create_tables.sql
002_create_rls_policies.sql
003_create_functions.sql
```

Or if using the Supabase CLI:

```bash
cd ~/koi-app
npx supabase db push
```

### 3.3 Enable Phone Auth

In the Supabase dashboard:
1. Go to **Authentication > Providers**
2. Enable **Phone** provider
3. Set SMS template: `Your Koi verification code is {{.Code}}`
4. Set OTP expiry: 5 minutes

---

## 4. Set Up the Voice Agent (Python)

```bash
cd ~/koi-app/agent

# Install dependencies
poetry install

# Verify installation
poetry run python -c "import httpx; import asyncpg; print('Dependencies OK')"

# Run the agent in development mode
poetry run python src/main.py dev
```

The agent should start and wait for LiveKit room connections. You will see output like:
```
INFO: Worker started, waiting for room connections...
```

### Testing the Agent

```bash
cd ~/koi-app/agent

# Run all tests
poetry run pytest

# Run only unit tests
poetry run pytest -m unit

# Run only integration tests
poetry run pytest -m integration

# Run with coverage report
poetry run pytest --cov=src --cov-report=term-missing
```

---

## 5. Set Up the Mobile App (React Native / Expo)

```bash
cd ~/koi-app/mobile/KoiApp

# Install dependencies
npm install

# Start the Expo development server
npx expo start
```

### Running on iOS Simulator
1. Make sure Xcode is installed with iOS simulators
2. Press `i` in the Expo terminal to open on iOS simulator
3. The app should launch with the onboarding screen

### Running on Physical Device (Recommended for Voice)
1. Install the **Expo Go** app on your iPhone
2. Scan the QR code shown in the Expo terminal
3. The app will load on your device
4. Voice features only work on physical devices (simulator has no microphone)

---

## 6. Run All Components Together

You need three terminal windows:

**Terminal 1 -- Voice Agent:**
```bash
cd ~/koi-app/agent
poetry run python src/main.py dev
```

**Terminal 2 -- Mobile App:**
```bash
cd ~/koi-app/mobile/KoiApp
npx expo start
```

**Terminal 3 -- (Optional) Supabase Edge Functions:**
```bash
cd ~/koi-app
npx supabase functions serve
```

### Verification Steps
1. Open the app on your phone
2. Enter your phone number and verify with OTP
3. Set your name and companion name
4. Tap "Start Talking"
5. Speak into your phone
6. Koi should respond in voice within 3 seconds

---

## 7. Development Workflow

### Git Branch Strategy
```
main           -- production-ready (protected)
  develop      -- integration branch
    feat/...   -- feature branches
```

### Creating a Feature Branch
```bash
git checkout develop
git pull
git checkout -b feat/my-feature
# ... make changes ...
git add -A
git commit -m "feat(agent): add my feature"
git push -u origin feat/my-feature
```

### Running Linters

**Python:**
```bash
cd ~/koi-app/agent
poetry run black src/ tests/
poetry run ruff check src/ tests/
poetry run mypy src/
```

**TypeScript:**
```bash
cd ~/koi-app/mobile/KoiApp
npx eslint src/
npx prettier --check src/
```

---

## 8. Testing the LiveKit Connection

If you want to test the voice agent without the mobile app:

1. Go to [agents-playground.livekit.io](https://agents-playground.livekit.io)
2. Connect using your LiveKit project credentials
3. Allow microphone access
4. Speak -- the agent should respond

---

## 9. Useful Commands Reference

| What | Command |
|------|---------|
| Run agent | `cd ~/koi-app/agent && poetry run python src/main.py dev` |
| Run mobile | `cd ~/koi-app/mobile/KoiApp && npx expo start` |
| Run Python tests | `cd ~/koi-app/agent && poetry run pytest` |
| Run Python tests with coverage | `cd ~/koi-app/agent && poetry run pytest --cov=src` |
| Format Python | `cd ~/koi-app/agent && poetry run black src/ tests/` |
| Lint Python | `cd ~/koi-app/agent && poetry run ruff check src/` |
| Type check Python | `cd ~/koi-app/agent && poetry run mypy src/` |
| Install Python deps | `cd ~/koi-app/agent && poetry install` |
| Install JS deps | `cd ~/koi-app/mobile/KoiApp && npm install` |
| Supabase migrations | `npx supabase db push` |
| Supabase edge functions | `npx supabase functions serve` |

---

## Common Errors

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for solutions to common issues.
