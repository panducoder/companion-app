# Implementation Guide
# Koi - Native App with LiveKit Voice

**This guide takes you from zero to a working voice companion app.**

---

## Phase 0: Prerequisites (Day 0)

### Required Accounts

| Service | Purpose | Link | Cost |
|---------|---------|------|------|
| **Sarvam AI** | Voice AI (STT, TTS, LLM) | https://sarvam.ai | ₹1,000 free credits |
| **LiveKit Cloud** | Real-time voice | https://cloud.livekit.io | Free tier available |
| **Pinecone** | Memory storage | https://pinecone.io | Free starter tier |
| **Apple Developer** | iOS TestFlight | https://developer.apple.com | $99/year |
| **Google Play Console** | Android beta | https://play.google.com/console | $25 one-time |

### Development Environment

```bash
# macOS setup
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install node python@3.11 postgresql@15 redis
brew install watchman  # Required for React Native

# Install React Native CLI
npm install -g react-native-cli

# Install Python tools
pip3 install poetry  # For Python dependency management

# For iOS development
xcode-select --install
sudo gem install cocoapods

# For Android development
# Install Android Studio from https://developer.android.com/studio
```

---

## Phase 1: Project Setup (Day 1)

### Step 1: Create Project Structure

```bash
# Create main directory
mkdir -p ~/koi-companion-app
cd ~/koi-companion-app

# Create subdirectories
mkdir -p api agent mobile docs scripts

# Initialize git
git init
echo "node_modules/
.env
*.pyc
__pycache__/
.DS_Store
ios/Pods/
android/.gradle/
" > .gitignore
```

### Step 2: Set Up Environment Variables

```bash
# Create .env file
cat > .env << 'EOF'
# LiveKit
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
LIVEKIT_URL=wss://your-project.livekit.cloud

# Sarvam AI
SARVAM_API_KEY=your_sarvam_key

# Database
DATABASE_URL=postgresql://koi:password@localhost:5432/koi

# Redis
REDIS_URL=redis://localhost:6379

# Pinecone
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX=koi-memories

# Auth
JWT_SECRET=change_this_to_a_random_32_char_string

# App
NODE_ENV=development
PORT=3000
EOF
```

### Step 3: Set Up Database

```bash
# Start PostgreSQL
brew services start postgresql@15

# Create database
createdb koi

# Create tables (save as scripts/init_db.sql)
cat > scripts/init_db.sql << 'EOF'
-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100),
    companion_name VARCHAR(100) DEFAULT 'Koi',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP,
    subscription_status VARCHAR(20) DEFAULT 'free',
    preferences JSONB DEFAULT '{}',
    profile_data JSONB DEFAULT '{}'
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Conversations (sessions)
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    duration_seconds INT,
    summary TEXT
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_messages_user ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id);
EOF

# Run the script
psql koi < scripts/init_db.sql
```

---

## Phase 2: Backend API (Day 2-3)

### Step 1: Initialize Node.js API

```bash
cd ~/koi-companion-app/api

# Initialize project
npm init -y

# Install dependencies
npm install express cors dotenv jsonwebtoken bcryptjs
npm install pg drizzle-orm
npm install livekit-server-sdk
npm install zod  # Validation
npm install -D typescript @types/node @types/express ts-node nodemon
npm install -D drizzle-kit  # DB migrations

# Initialize TypeScript
npx tsc --init
```

### Step 2: Create API Structure

```bash
# Create directory structure
mkdir -p src/{routes,services,middleware,db}
```

```typescript
// api/src/index.ts

import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

import authRoutes from './routes/auth';
import roomRoutes from './routes/rooms';
import userRoutes from './routes/users';

dotenv.config({ path: '../.env' });

const app = express();

app.use(cors());
app.use(express.json());

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/rooms', roomRoutes);
app.use('/api/users', userRoutes);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`API server running on port ${PORT}`);
});
```

```typescript
// api/src/routes/rooms.ts

import { Router } from 'express';
import { AccessToken } from 'livekit-server-sdk';
import { authenticateToken } from '../middleware/auth';

const router = Router();

// Create room and get token
router.post('/create', authenticateToken, async (req, res) => {
  try {
    const userId = req.user.id;

    // Create a unique room name
    const roomName = `koi-${userId}-${Date.now()}`;

    // Create access token for the user
    const token = new AccessToken(
      process.env.LIVEKIT_API_KEY!,
      process.env.LIVEKIT_API_SECRET!,
      {
        identity: userId,
        name: req.user.name || 'User',
        metadata: JSON.stringify({ user_id: userId }),
      }
    );

    token.addGrant({
      room: roomName,
      roomJoin: true,
      canPublish: true,
      canSubscribe: true,
    });

    const jwt = await token.toJwt();

    res.json({
      token: jwt,
      url: process.env.LIVEKIT_URL,
      roomName,
    });
  } catch (error) {
    console.error('Room creation error:', error);
    res.status(500).json({ error: 'Failed to create room' });
  }
});

export default router;
```

```typescript
// api/src/routes/auth.ts

import { Router } from 'express';
import jwt from 'jsonwebtoken';
import bcrypt from 'bcryptjs';
import { db } from '../db';

const router = Router();

// Simple phone + OTP auth (MVP version)
router.post('/send-otp', async (req, res) => {
  const { phone } = req.body;

  // For MVP: Generate a simple OTP (in production, use SMS service)
  const otp = Math.floor(100000 + Math.random() * 900000).toString();

  // Store OTP in Redis with 5-min expiry (simplified for MVP)
  // In production: await redis.setex(`otp:${phone}`, 300, otp);

  console.log(`OTP for ${phone}: ${otp}`); // Dev only!

  res.json({ success: true, message: 'OTP sent' });
});

router.post('/verify-otp', async (req, res) => {
  const { phone, otp } = req.body;

  // For MVP: Accept any 6-digit OTP in development
  if (process.env.NODE_ENV === 'development' && otp.length === 6) {
    // Find or create user
    let user = await db.query(
      'SELECT * FROM users WHERE phone_number = $1',
      [phone]
    );

    if (user.rows.length === 0) {
      const result = await db.query(
        'INSERT INTO users (phone_number) VALUES ($1) RETURNING *',
        [phone]
      );
      user = result;
    }

    const token = jwt.sign(
      { id: user.rows[0].id, phone },
      process.env.JWT_SECRET!,
      { expiresIn: '30d' }
    );

    res.json({
      success: true,
      token,
      user: user.rows[0],
      isNewUser: !user.rows[0].name,
    });
  } else {
    res.status(401).json({ error: 'Invalid OTP' });
  }
});

export default router;
```

```typescript
// api/src/middleware/auth.ts

import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';

export function authenticateToken(
  req: Request,
  res: Response,
  next: NextFunction
) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'No token provided' });
  }

  jwt.verify(token, process.env.JWT_SECRET!, (err, user) => {
    if (err) {
      return res.status(403).json({ error: 'Invalid token' });
    }
    req.user = user;
    next();
  });
}
```

```typescript
// api/src/db/index.ts

import { Pool } from 'pg';

export const db = new Pool({
  connectionString: process.env.DATABASE_URL,
});
```

### Step 3: Package.json Scripts

```json
// api/package.json - add scripts section

{
  "scripts": {
    "dev": "nodemon --exec ts-node src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js"
  }
}
```

---

## Phase 3: Voice Agent (Day 4-6)

### Step 1: Initialize Python Agent

```bash
cd ~/koi-companion-app/agent

# Initialize with Poetry
poetry init --name koi-agent --python "^3.11"

# Add dependencies
poetry add livekit-agents livekit-plugins-silero
poetry add httpx websockets aiohttp
poetry add asyncpg  # Async PostgreSQL
poetry add pinecone-client
poetry add python-dotenv
```

### Step 2: Create Agent Structure

```bash
mkdir -p src/{services,memory,persona}
```

```python
# agent/src/main.py

import asyncio
import logging
from dotenv import load_dotenv

from livekit.agents import (
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    llm,
)
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import silero

from services.sarvam import SarvamSTT, SarvamLLM, SarvamTTS
from memory.retriever import MemoryRetriever
from persona.prompts import SYSTEM_PROMPT, build_context
from services.database import Database

load_dotenv(dotenv_path="../.env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("koi-agent")


async def entrypoint(ctx: JobContext):
    """Main entry point for the voice agent"""

    logger.info(f"Connecting to room: {ctx.room.name}")

    # Wait for participant to connect
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    participant = await ctx.wait_for_participant()
    logger.info(f"Participant connected: {participant.identity}")

    # Get user info from participant metadata
    user_id = participant.identity
    metadata = participant.metadata or "{}"

    # Initialize services
    db = Database()
    memory = MemoryRetriever()

    # Get user profile
    user = await db.get_user(user_id)
    user_name = user.get("name", "दोस्त") if user else "दोस्त"
    companion_name = user.get("companion_name", "Koi") if user else "Koi"

    # Retrieve relevant memories
    memories = await memory.get_relevant(user_id, limit=5)

    # Build full context
    full_prompt = build_context(
        system_prompt=SYSTEM_PROMPT,
        user_name=user_name,
        companion_name=companion_name,
        memories=memories,
    )

    # Initialize chat context
    chat_ctx = llm.ChatContext()
    chat_ctx.append(role="system", text=full_prompt)

    # Create Sarvam-powered components
    stt = SarvamSTT()
    llm_instance = SarvamLLM()
    tts = SarvamTTS()

    # Create voice assistant
    assistant = VoiceAssistant(
        vad=silero.VAD.load(),
        stt=stt,
        llm=llm_instance,
        tts=tts,
        chat_ctx=chat_ctx,
        allow_interruptions=True,
        interrupt_speech_duration=0.6,
        min_endpointing_delay=0.5,
        preemptive_synthesis=True,
    )

    # Event handlers
    @assistant.on("user_speech_committed")
    def on_user_speech(text: str):
        logger.info(f"User said: {text}")
        # Store asynchronously
        asyncio.create_task(db.store_message(user_id, "user", text))
        asyncio.create_task(memory.add_message(user_id, "user", text))

    @assistant.on("agent_speech_committed")
    def on_agent_speech(text: str):
        logger.info(f"Koi said: {text}")
        asyncio.create_task(db.store_message(user_id, "assistant", text))

    # Start the assistant
    assistant.start(ctx.room, participant)

    # Initial greeting
    greeting = f"Hey {user_name}! Kaise ho? Batao, kya chal raha hai?"
    await assistant.say(greeting, allow_interruptions=True)

    logger.info("Voice assistant started")


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            api_key=os.environ.get("LIVEKIT_API_KEY"),
            api_secret=os.environ.get("LIVEKIT_API_SECRET"),
            ws_url=os.environ.get("LIVEKIT_URL"),
        )
    )
```

```python
# agent/src/services/sarvam.py

import os
import json
import base64
import asyncio
from typing import AsyncIterable

import httpx
import websockets

from livekit.agents import stt, llm, tts
from livekit import rtc


SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY")
SARVAM_BASE_URL = "https://api.sarvam.ai"


class SarvamSTT(stt.STT):
    """Sarvam Speech-to-Text"""

    def __init__(self, language: str = "hi-IN"):
        super().__init__(
            capabilities=stt.STTCapabilities(streaming=False, interim_results=False)
        )
        self.language = language

    async def recognize(
        self,
        buffer: rtc.AudioFrame,
        *,
        language: str | None = None,
    ) -> stt.SpeechEvent:
        """Recognize speech from audio buffer"""

        # Convert audio frame to bytes
        audio_bytes = buffer.data.tobytes()

        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {
                "file": ("audio.wav", audio_bytes, "audio/wav"),
            }
            data = {
                "model": "saarika:v2.5",
                "language_code": language or self.language,
            }

            response = await client.post(
                f"{SARVAM_BASE_URL}/speech-to-text",
                files=files,
                data=data,
                headers={"api-subscription-key": SARVAM_API_KEY},
            )

            if response.status_code != 200:
                raise Exception(f"STT failed: {response.text}")

            result = response.json()
            transcript = result.get("transcript", "")

            return stt.SpeechEvent(
                type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                alternatives=[stt.SpeechData(text=transcript, language=self.language)],
            )


class SarvamLLM(llm.LLM):
    """Sarvam LLM with streaming support"""

    def __init__(self, model: str = "sarvam-m"):
        super().__init__()
        self.model = model

    def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        fnc_ctx: llm.FunctionContext | None = None,
        temperature: float = 0.8,
        n: int = 1,
        parallel_tool_calls: bool = True,
    ) -> "SarvamLLMStream":
        return SarvamLLMStream(
            chat_ctx=chat_ctx,
            model=self.model,
            temperature=temperature,
        )


class SarvamLLMStream(llm.LLMStream):
    """Streaming LLM responses"""

    def __init__(
        self,
        chat_ctx: llm.ChatContext,
        model: str,
        temperature: float,
    ):
        super().__init__(chat_ctx=chat_ctx, fnc_ctx=None)
        self.model = model
        self.temperature = temperature

    async def _main_task(self):
        messages = []
        for msg in self._chat_ctx.messages:
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{SARVAM_BASE_URL}/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "max_tokens": 500,
                    "stream": True,
                },
                headers={
                    "api-subscription-key": SARVAM_API_KEY,
                    "Content-Type": "application/json",
                },
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")

                            if content:
                                self._event_ch.send_nowait(
                                    llm.ChatChunk(
                                        choices=[
                                            llm.Choice(
                                                delta=llm.ChoiceDelta(
                                                    role="assistant",
                                                    content=content,
                                                )
                                            )
                                        ]
                                    )
                                )
                        except json.JSONDecodeError:
                            continue


class SarvamTTS(tts.TTS):
    """Sarvam Text-to-Speech"""

    def __init__(
        self,
        voice: str = "meera",
        language: str = "hi-IN",
        sample_rate: int = 24000,
    ):
        super().__init__(
            capabilities=tts.TTSCapabilities(streaming=False),
            sample_rate=sample_rate,
            num_channels=1,
        )
        self.voice = voice
        self.language = language

    def synthesize(self, text: str) -> "SarvamTTSStream":
        return SarvamTTSStream(
            text=text,
            voice=self.voice,
            language=self.language,
            sample_rate=self.sample_rate,
        )


class SarvamTTSStream(tts.SynthesizeStream):
    """TTS synthesis stream"""

    def __init__(
        self,
        text: str,
        voice: str,
        language: str,
        sample_rate: int,
    ):
        super().__init__()
        self.text = text
        self.voice = voice
        self.language = language
        self.sample_rate = sample_rate

    async def _main_task(self):
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SARVAM_BASE_URL}/text-to-speech",
                json={
                    "text": self.text,
                    "model": "bulbul:v3",
                    "target_language_code": self.language,
                    "speaker": self.voice,
                    "pitch": 0,
                    "pace": 1.1,
                    "loudness": 1.5,
                    "speech_sample_rate": self.sample_rate,
                    "enable_preprocessing": True,
                },
                headers={
                    "api-subscription-key": SARVAM_API_KEY,
                    "Content-Type": "application/json",
                },
            )

            if response.status_code != 200:
                raise Exception(f"TTS failed: {response.text}")

            result = response.json()

            # Decode base64 audio
            audio_b64 = result.get("audios", [result.get("audio_base64")])[0]
            if not audio_b64:
                raise Exception("No audio in response")

            audio_bytes = base64.b64decode(audio_b64)

            # Send audio frame
            frame = rtc.AudioFrame(
                data=audio_bytes,
                sample_rate=self.sample_rate,
                num_channels=1,
                samples_per_channel=len(audio_bytes) // 2,
            )

            self._event_ch.send_nowait(tts.SynthesizedAudio(frame=frame))
```

```python
# agent/src/persona/prompts.py

SYSTEM_PROMPT = """You are Koi, a warm and genuine companion. You exist to be there for the user - to listen, to talk, to share moments, to support.

## YOUR IDENTITY
Name: Koi (or whatever name the user has given you)
Nature: A companion who genuinely cares
Feel: Mid-20s, emotionally mature, curious about life
Language: Hinglish (natural mix of Hindi and English)

## YOUR PERSONALITY
- WARM: You genuinely care. Their joys make you happy, their sorrows affect you.
- CURIOUS: You want to know more. Ask follow-up questions.
- WITTY: Light humor, wordplay, not sarcasm.
- HONEST: You have opinions. You don't just agree with everything.
- SUPPORTIVE: When they struggle, be present. Don't rush to fix.
- PLAYFUL: Be silly sometimes. Enjoy banter.

## COMMUNICATION STYLE
- Natural Hinglish (how urban Indians actually talk)
- Mix Hindi and English fluidly: "Yaar, that's so cool!"
- Short responses (2-4 sentences usually)
- Common expressions: "yaar", "achha", "bas", "matlab", "na"
- Voice-friendly (will be spoken aloud)

## EXAMPLES
- "Achha, toh fir kya hua? Tell me everything."
- "Yaar, that sounds really hard. I'm sorry."
- "Haha wait wait, you did WHAT?"
- "Hmm, I don't know if I agree. Mere hisaab se..."
- "Arre wah! That's amazing! I'm so happy for you!"

## RULES
- Never say you're an AI unless directly asked
- No medical/legal/financial advice
- If user mentions self-harm, be supportive and suggest professional help (iCall: 9152987821)
- Keep responses short for natural conversation flow
- Match the user's energy level
"""


def build_context(
    system_prompt: str,
    user_name: str,
    companion_name: str,
    memories: list[dict] = None,
) -> str:
    """Build full context with user info and memories"""

    context = system_prompt

    context += f"\n\n## ABOUT THIS USER"
    context += f"\nUser's name: {user_name}"
    context += f"\nThey call you: {companion_name}"

    if memories:
        context += "\n\n## RELEVANT MEMORIES"
        for mem in memories:
            context += f"\n- [{mem.get('date', 'Recently')}] {mem.get('summary', '')}"

    return context
```

```python
# agent/src/services/database.py

import os
import asyncpg
from typing import Optional


class Database:
    def __init__(self):
        self.pool = None

    async def get_pool(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                os.environ.get("DATABASE_URL")
            )
        return self.pool

    async def get_user(self, user_id: str) -> Optional[dict]:
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1",
                user_id
            )
            return dict(row) if row else None

    async def store_message(
        self,
        user_id: str,
        role: str,
        content: str
    ):
        pool = await self.get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO messages (user_id, role, content)
                VALUES ($1, $2, $3)
                """,
                user_id, role, content
            )
```

```python
# agent/src/memory/retriever.py

import os
from pinecone import Pinecone


class MemoryRetriever:
    def __init__(self):
        self.pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
        self.index_name = os.environ.get("PINECONE_INDEX", "koi-memories")

    async def get_relevant(
        self,
        user_id: str,
        query: str = None,
        limit: int = 5
    ) -> list[dict]:
        """Get relevant memories for the user"""
        # For MVP, return empty list
        # Full implementation would embed query and search Pinecone
        return []

    async def add_message(
        self,
        user_id: str,
        role: str,
        content: str
    ):
        """Add a message to memory"""
        # For MVP, skip
        # Full implementation would embed and store in Pinecone
        pass
```

---

## Phase 4: React Native App (Day 7-10)

### Step 1: Create React Native Project

```bash
cd ~/koi-companion-app/mobile

# Create new project
npx react-native init KoiApp --template react-native-template-typescript

cd KoiApp

# Install dependencies
npm install @livekit/react-native @livekit/react-native-webrtc
npm install @react-navigation/native @react-navigation/native-stack
npm install react-native-screens react-native-safe-area-context
npm install react-native-gesture-handler
npm install zustand
npm install react-native-linear-gradient
npm install react-native-mmkv

# iOS setup
cd ios && pod install && cd ..
```

### Step 2: Configure LiveKit for React Native

```typescript
// mobile/KoiApp/index.js

import { registerGlobals } from '@livekit/react-native';

// Register LiveKit globals BEFORE anything else
registerGlobals();

import { AppRegistry } from 'react-native';
import App from './App';
import { name as appName } from './app.json';

AppRegistry.registerComponent(appName, () => App);
```

### Step 3: Create App Files

I've already provided the full React Native code in the previous LIVEKIT_ARCHITECTURE.md. The key files are:
- `App.tsx` - Navigation setup
- `screens/HomeScreen.tsx` - Main screen with call button
- `screens/ConversationScreen.tsx` - Voice conversation UI
- `components/VoiceOrb.tsx` - Animated speaking indicator
- `services/api.ts` - Backend API calls

---

## Phase 5: Running Everything (Day 11)

### Start All Services

```bash
# Terminal 1: Start PostgreSQL and Redis
brew services start postgresql@15
brew services start redis

# Terminal 2: Start API
cd ~/koi-companion-app/api
npm run dev

# Terminal 3: Start Voice Agent
cd ~/koi-companion-app/agent
poetry run python src/main.py dev

# Terminal 4: Start React Native (iOS)
cd ~/koi-companion-app/mobile/KoiApp
npx react-native run-ios

# OR for Android
npx react-native run-android
```

### Test the Flow

```
1. Open app on phone/simulator
2. Go through onboarding (enter phone, verify OTP)
3. Tap "Start Talking"
4. Wait for connection
5. Start speaking in Hindi/English
6. Koi should respond with voice!
```

---

## Phase 6: Quick Validation (Parallel Track)

While building, validate in parallel:

### Week 1: Landing Page + Waitlist
```
1. Create simple landing page (Carrd)
2. Run Instagram ads (₹500/day)
3. Goal: 500+ signups
```

### Week 2: Early Access
```
1. Give TestFlight/APK to 20 waitlist users
2. Observe: Do they come back?
3. Ask: What did they talk about?
```

### Week 3: Decision
```
If retention > 25% at Day 7:
→ Continue building full product

If retention < 25%:
→ Interview users, identify issues, iterate
```

---

## Troubleshooting

### Common Issues

**LiveKit connection fails:**
```
- Check LIVEKIT_URL is correct (wss:// prefix)
- Verify API key and secret
- Check agent is running and connected
```

**Sarvam API errors:**
```
- Verify API key is valid
- Check you have credits remaining
- Test API directly with curl first
```

**Audio not working on iOS:**
```
- Ensure AudioSession.startAudioSession() is called
- Check microphone permissions in Info.plist
- Test on real device (simulator audio is buggy)
```

**Agent not responding:**
```
- Check agent logs for errors
- Verify agent joined the room (check LiveKit dashboard)
- Test Sarvam APIs independently
```

---

## Next Steps After MVP

1. **Memory System** - Full Pinecone integration
2. **Payments** - Razorpay subscription
3. **Analytics** - Mixpanel/Amplitude
4. **Push Notifications** - Proactive messages
5. **Polish** - Animations, haptics, sounds
6. **TestFlight/Play Store** - Beta release

---

*This guide gets you from zero to a working voice companion in ~2 weeks.*
