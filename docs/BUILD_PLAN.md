# Koi Voice Companion - Detailed Build Plan
# (Designed for parallel agent execution)

---

## Project Summary

**What:** A voice-first AI companion app for India. Users tap a button, talk to Koi like a friend, and Koi responds in real-time with natural Hinglish voice.

**Stack:**
- **Mobile App:** React Native (Expo) with LiveKit SDK
- **Voice Agent:** Python with LiveKit Agents framework + Sarvam AI
- **Backend:** Supabase (Auth + Database + Edge Functions)
- **Memory:** Pinecone vector database
- **Test Device:** iPhone (TestFlight for beta)

**Quality Bar:** Production-grade. No placeholder UIs, no mock data, no "TODO later" hacks.

---

## Architecture

```
┌────────────────────────────────┐
│       MOBILE APP (Expo)        │
│                                │
│  Screens:                      │
│  ├── Onboarding (phone auth)   │
│  ├── Home (talk button)        │
│  ├── Conversation (voice orb)  │
│  ├── History (past talks)      │
│  └── Settings (privacy, prefs) │
│                                │
│  Connects to:                  │
│  ├── Supabase (auth + data)    │
│  └── LiveKit (real-time voice) │
└──────────────┬─────────────────┘
               │ WebRTC audio stream
               ▼
┌────────────────────────────────┐
│       LIVEKIT CLOUD            │
│  (Real-time media routing)     │
└──────────────┬─────────────────┘
               │ WebSocket
               ▼
┌────────────────────────────────┐
│     VOICE AGENT (Python)       │
│                                │
│  Pipeline:                     │
│  User audio                    │
│    → Silero VAD (speech detect)│
│    → Sarvam STT (speech→text)  │
│    → Memory retrieval (Pinecone│
│    → Sarvam LLM (generate resp)│
│    → Sarvam TTS (text→speech)  │
│    → Audio back to user        │
│                                │
│  Connects to:                  │
│  ├── LiveKit (audio stream)    │
│  ├── Sarvam APIs (AI pipeline) │
│  ├── Supabase DB (user data)   │
│  └── Pinecone (memories)       │
└────────────────────────────────┘

┌────────────────────────────────┐
│       SUPABASE                 │
│                                │
│  ├── Auth (phone OTP)          │
│  ├── PostgreSQL Database       │
│  │   ├── users table           │
│  │   ├── conversations table   │
│  │   └── messages table        │
│  └── Edge Functions            │
│      └── generate-room-token   │
└────────────────────────────────┘

┌────────────────────────────────┐
│       PINECONE                 │
│  (Vector DB for memories)      │
│                                │
│  Index: koi-memories           │
│  Dimensions: 1024              │
│  Metric: cosine                │
└────────────────────────────────┘
```

---

## Workstreams (Parallelizable)

These 4 workstreams can be built in parallel by separate agents. The interfaces between them are defined below so each agent knows what to produce and consume.

---

### WORKSTREAM 1: Voice Agent (Python)
**Location:** `~/koi-app/agent/`
**Language:** Python 3.11+
**Dependencies on other workstreams:** None (can test independently via LiveKit Playground)

#### Directory Structure
```
agent/
├── pyproject.toml              # Poetry dependency file
├── .env                        # Environment variables (symlink to root)
├── Dockerfile                  # For deployment
├── README.md                   # Agent-specific docs
└── src/
    ├── __init__.py
    ├── main.py                 # Entry point - LiveKit agent worker
    ├── services/
    │   ├── __init__.py
    │   └── sarvam.py           # Sarvam STT, LLM, TTS wrappers
    ├── persona/
    │   ├── __init__.py
    │   └── prompts.py          # System prompt + context builder
    ├── memory/
    │   ├── __init__.py
    │   ├── retriever.py        # Fetch relevant memories from Pinecone
    │   └── storage.py          # Store new memories to Pinecone
    └── db/
        ├── __init__.py
        └── client.py           # Supabase/PostgreSQL client for user data
```

#### File Specifications

**`pyproject.toml`** - Dependencies:
```
python = "^3.11"
livekit-agents = "^0.12"
livekit-plugins-silero = "^0.7"
httpx = "^0.27"
asyncpg = "^0.29"
pinecone-client = "^3"
python-dotenv = "^1.0"
```

**`src/main.py`** - Entry point:
- Register as LiveKit agent worker
- On new room: extract user_id from participant metadata
- Fetch user profile from Supabase DB
- Fetch relevant memories from Pinecone
- Build system prompt with user context + memories
- Create VoiceAssistant with Sarvam STT/LLM/TTS + Silero VAD
- Configure: allow_interruptions=True, min_endpointing_delay=0.5s
- On user_speech_committed: store message in DB + update Pinecone async
- On agent_speech_committed: store message in DB async
- Greet user by name on connect

**`src/services/sarvam.py`** - Sarvam API wrappers:
- **SarvamSTT class** (implements livekit.agents.stt.STT):
  - Uses Sarvam Saarika v2.5 model
  - Language: hi-IN (with Hinglish support)
  - Endpoint: POST /speech-to-text
  - Accepts audio buffer, returns transcript
  - Must handle: timeouts (10s), retries (2x), empty audio

- **SarvamLLM class** (implements livekit.agents.llm.LLM):
  - Uses Sarvam-M model
  - Streaming responses enabled
  - Endpoint: POST /chat/completions with stream=true
  - Temperature: 0.8
  - Max tokens: 300 (keep responses short for voice)
  - Must handle: streaming SSE parsing, connection drops

- **SarvamTTS class** (implements livekit.agents.tts.TTS):
  - Uses Sarvam Bulbul v3 model
  - Voice: "meera" (warm, natural)
  - Language: hi-IN
  - Pace: 1.1 (slightly faster for natural feel)
  - Endpoint: POST /text-to-speech
  - Returns base64 audio → decode to AudioFrame
  - Must handle: long text (chunk into sentences), empty responses

**`src/persona/prompts.py`** - System prompt:
- Contains the full Koi persona (from PROMPT_ENGINEERING.md)
- `build_context(user, memories)` function that assembles:
  - Base system prompt (personality, rules, communication style)
  - User profile section (name, companion_name, relationship_stage)
  - Relevant memories section (last 5 relevant past conversations)
  - Current context (time of day, days since first conversation)
- Keep total prompt under 2000 tokens

**`src/memory/retriever.py`** - Memory retrieval:
- Connect to Pinecone index "koi-memories"
- `get_relevant(user_id, query_text, top_k=5)`:
  - Embed query_text using Sarvam embedding or simple TF-IDF (MVP)
  - Query Pinecone with user_id filter
  - Return list of memory summaries
- `store_conversation(user_id, messages)`:
  - Summarize conversation (use Sarvam LLM)
  - Embed summary
  - Upsert to Pinecone with metadata (date, topic, emotional_tone)

**`src/db/client.py`** - Database operations:
- Connect to Supabase PostgreSQL via asyncpg
- `get_user(user_id)` → user record
- `store_message(user_id, role, content)` → insert into messages
- `create_conversation(user_id)` → new conversation record
- `end_conversation(conversation_id, summary)` → update end time

#### Testing the Agent
```bash
# Run agent locally
cd ~/koi-app/agent
poetry install
poetry run python src/main.py dev

# Test via LiveKit Playground (browser):
# 1. Go to https://agents-playground.livekit.io
# 2. Connect to your LiveKit project
# 3. Speak into microphone
# 4. Agent should respond in voice
```

#### Success Criteria
- [ ] Agent starts and connects to LiveKit
- [ ] Responds to speech in Hinglish
- [ ] Latency from end of speech to first response audio: <3 seconds
- [ ] No crashes on 5-minute conversation
- [ ] Handles user interruption gracefully

---

### WORKSTREAM 2: Mobile App (React Native / Expo)
**Location:** `~/koi-app/mobile/KoiApp/`
**Language:** TypeScript
**Dependencies:** Needs Supabase project URL (from Workstream 3) and LiveKit URL (from account setup)

#### Directory Structure
```
KoiApp/
├── app.json                    # Expo config
├── App.tsx                     # Root component
├── babel.config.js
├── tsconfig.json
├── assets/
│   ├── icon.png                # App icon (1024x1024)
│   ├── splash.png              # Splash screen
│   └── fonts/                  # Custom fonts if needed
└── src/
    ├── screens/
    │   ├── OnboardingScreen.tsx    # Phone auth + name setup
    │   ├── HomeScreen.tsx          # Main screen
    │   ├── ConversationScreen.tsx  # Voice call UI
    │   ├── HistoryScreen.tsx       # Past conversations
    │   └── SettingsScreen.tsx      # Preferences + privacy
    ├── components/
    │   ├── VoiceOrb.tsx            # Animated orb (core visual)
    │   ├── TranscriptBubble.tsx    # Live transcript display
    │   ├── CallControls.tsx        # Mute, end, speaker buttons
    │   ├── ConsentModal.tsx        # Privacy consent overlay
    │   └── LoadingScreen.tsx       # Connection loading state
    ├── services/
    │   ├── supabase.ts             # Supabase client config
    │   ├── api.ts                  # Backend API calls
    │   └── livekit.ts              # LiveKit room management
    ├── stores/
    │   ├── authStore.ts            # Auth state (zustand)
    │   └── settingsStore.ts        # User preferences
    ├── theme/
    │   ├── colors.ts               # Color palette
    │   ├── typography.ts           # Font styles
    │   └── spacing.ts              # Layout constants
    └── utils/
        ├── haptics.ts              # Haptic feedback helpers
        └── permissions.ts          # Microphone permission
```

#### Screen Specifications

**OnboardingScreen.tsx** (3-step flow):
```
Step 1: Welcome
- Full-screen dark gradient background
- Logo animation (Koi text fade in)
- "Someone who's always there" tagline
- "Get Started" button → Step 2

Step 2: Phone Auth
- Phone number input (Indian format +91)
- "Send OTP" button
- OTP input (6 digits, auto-advance)
- "Verify" button
- Uses Supabase phone auth

Step 3: Personalize
- "What should I call you?" → text input for user's name
- "And what would you like to call me?" → default "Koi", editable
- "Start talking" button → Home screen
- Save to Supabase user profile
```

**HomeScreen.tsx:**
```
Layout:
- Status bar: dark content
- Top: "Hey {name}" greeting + settings icon
- Center: Large animated orb (breathing animation, idle state)
- Center: "{companionName}" text + "Ready to talk" subtitle
- Center: "Start Talking" button (gradient, prominent)
- Bottom: Recent conversations list (date, duration)
  - Tap to see transcript

Interactions:
- "Start Talking" → request mic permission → navigate to ConversationScreen
- Settings icon → SettingsScreen
- Recent conversation → HistoryScreen with that conversation
```

**ConversationScreen.tsx:**
```
Layout:
- Full screen dark gradient
- Center: VoiceOrb component (responds to audio state)
- Center below orb: "{companionName}" + connection status
- Bottom: TranscriptBubble (shows last spoken text, fades)
- Bottom: CallControls (mute, end call)

Behavior:
1. On mount: Call API to get LiveKit room token
2. Connect to LiveKit room
3. Start audio session
4. Show "Connecting..." state with gentle pulse
5. When agent connects: Show "Listening..." state
6. When user speaks: Orb shows "listening" animation (green glow)
7. When agent speaks: Orb shows "speaking" animation (purple pulse)
8. When user taps "End": Disconnect, navigate back, save conversation

States:
- Connecting: Gentle pulse, "Connecting..."
- Listening: Green glow, "Listening..."
- Speaking: Purple animated pulse, Koi's name
- Error: Red tint, "Connection lost. Reconnecting..."
- Ended: Fade out, return to home

LiveKit Integration:
- Use @livekit/react-native LiveKitRoom component
- Publish microphone track
- Subscribe to agent audio track
- Monitor participant events for state changes
```

**SettingsScreen.tsx:**
```
Sections:
1. Profile
   - Your name (editable)
   - Companion name (editable)

2. Privacy
   - "Your data" explanation text
   - "Download my data" button
   - "Delete all my data" button (with confirmation)
   - "Privacy Policy" link

3. Voice
   - Voice selection (when multiple available)
   - Language preference

4. Account
   - Phone number (display only)
   - Subscription status
   - "Log out" button

5. About
   - Version number
   - "Report a problem" link
   - Credits
```

#### Design System

**Colors:**
```typescript
export const colors = {
  // Backgrounds
  bg: {
    primary: '#0A0A1A',      // Deep dark blue-black
    secondary: '#12122A',     // Slightly lighter
    card: '#1A1A3E',          // Card background
  },
  // Accent
  accent: {
    primary: '#7C5CFC',      // Purple (Koi's color)
    secondary: '#5B8DEF',    // Blue
    gradient: ['#7C5CFC', '#5B8DEF'], // Primary gradient
  },
  // Status
  status: {
    listening: '#34D399',    // Green
    speaking: '#A78BFA',     // Light purple
    error: '#EF4444',        // Red
    connecting: '#FBBF24',   // Amber
  },
  // Text
  text: {
    primary: '#FFFFFF',
    secondary: '#9CA3AF',
    muted: '#4B5563',
  },
  // Surface
  surface: {
    border: 'rgba(255,255,255,0.08)',
    overlay: 'rgba(0,0,0,0.5)',
  }
};
```

**Typography:**
```typescript
export const typography = {
  hero: { fontSize: 48, fontWeight: '700', lineHeight: 56 },
  h1: { fontSize: 28, fontWeight: '600', lineHeight: 34 },
  h2: { fontSize: 22, fontWeight: '600', lineHeight: 28 },
  body: { fontSize: 16, fontWeight: '400', lineHeight: 24 },
  caption: { fontSize: 14, fontWeight: '400', lineHeight: 20 },
  small: { fontSize: 12, fontWeight: '400', lineHeight: 16 },
};
```

#### VoiceOrb Component (Core Visual)

The VoiceOrb is the most important visual element. It should feel alive.

**States & Animations:**
```
IDLE (Home screen):
- Slow breathing animation (scale 1.0 → 1.03 → 1.0, 4 second cycle)
- Subtle gradient rotation (20s full rotation)
- Colors: accent.primary gradient

CONNECTING:
- Gentle pulse (scale 1.0 → 1.05, 1 second cycle)
- Amber glow
- Opacity: 0.7 → 0.9

LISTENING:
- Slight breathing (scale 1.0 → 1.02, 2 second cycle)
- Green glow ring
- Ring opacity pulses with ambient audio level

SPEAKING:
- Active pulse matching speech rhythm (scale 1.0 → 1.15 → 1.0)
- Frequency: fast, ~300ms cycle
- Purple/blue gradient
- Outer glow rings expand outward
- Multiple concentric rings with staggered animations

ERROR:
- Scale to 0.95
- Red tint overlay
- Single pulse then static
```

**Implementation approach:**
- Use `react-native-reanimated` for 60fps animations
- Use `Animated.Value` for scale, opacity, rotation
- Respond to LiveKit track events for state changes
- Use `expo-haptics` for subtle haptic feedback on state transitions

#### Expo Configuration

**app.json additions:**
```json
{
  "expo": {
    "name": "Koi",
    "slug": "koi-app",
    "version": "1.0.0",
    "orientation": "portrait",
    "userInterfaceStyle": "dark",
    "scheme": "koi",
    "ios": {
      "bundleIdentifier": "com.koi.companion",
      "supportsTablet": false,
      "infoPlist": {
        "NSMicrophoneUsageDescription": "Koi needs access to your microphone so you can have voice conversations.",
        "UIBackgroundModes": ["audio"]
      }
    },
    "android": {
      "package": "com.koi.companion",
      "permissions": ["RECORD_AUDIO"]
    },
    "plugins": [
      "@livekit/react-native-webrtc"
    ]
  }
}
```

#### Dependencies
```json
{
  "@livekit/react-native": "^2.0",
  "@livekit/react-native-webrtc": "^1.0",
  "@react-navigation/native": "^6",
  "@react-navigation/native-stack": "^6",
  "@supabase/supabase-js": "^2",
  "expo": "~50",
  "expo-av": "~14",
  "expo-haptics": "~13",
  "react-native-reanimated": "~3",
  "react-native-safe-area-context": "~4",
  "react-native-screens": "~3",
  "zustand": "^4"
}
```

#### Success Criteria
- [ ] App boots on iOS simulator without errors
- [ ] Can navigate between all screens
- [ ] Phone auth works (OTP via Supabase)
- [ ] VoiceOrb renders with smooth 60fps animations
- [ ] LiveKit room connects and publishes microphone
- [ ] Can hear agent audio through phone speaker
- [ ] Haptic feedback fires on button press
- [ ] Dark mode looks polished on iPhone SE through iPhone 15 Pro Max

---

### WORKSTREAM 3: Backend (Supabase)
**Location:** `~/koi-app/supabase/`
**Language:** SQL + TypeScript (Edge Functions)
**Dependencies:** None (can be set up independently)

#### What to Set Up in Supabase Dashboard

**1. Database Tables (SQL):**

```sql
-- Users table (extends Supabase auth.users)
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT,
    companion_name TEXT DEFAULT 'Koi',
    phone TEXT,
    relationship_stage TEXT DEFAULT 'early',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ,
    subscription_status TEXT DEFAULT 'free',
    subscription_expires_at TIMESTAMPTZ,
    preferences JSONB DEFAULT '{}',
    profile_data JSONB DEFAULT '{}'
);

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, phone)
    VALUES (NEW.id, NEW.phone);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- Conversations table
CREATE TABLE public.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    summary TEXT,
    emotional_tone TEXT
);

-- Messages table
CREATE TABLE public.messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES public.conversations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Row Level Security
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- Users can only access their own data
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can view own conversations"
    ON public.conversations FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can view own messages"
    ON public.messages FOR SELECT
    USING (auth.uid() = user_id);

-- Indexes
CREATE INDEX idx_conversations_user ON public.conversations(user_id);
CREATE INDEX idx_messages_conversation ON public.messages(conversation_id);
CREATE INDEX idx_messages_user ON public.messages(user_id);
```

**2. Authentication:**
- Enable Phone provider in Supabase Auth settings
- Configure SMS template: "Your Koi verification code is {{.Code}}"
- Set OTP expiry to 5 minutes
- Set rate limit to 5 attempts per phone per hour

**3. Edge Function: generate-room-token**

```typescript
// supabase/functions/generate-room-token/index.ts

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { AccessToken } from "npm:livekit-server-sdk";

serve(async (req) => {
  // Verify auth
  const authHeader = req.headers.get("Authorization")!;
  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_ANON_KEY")!,
    { global: { headers: { Authorization: authHeader } } }
  );

  const { data: { user }, error } = await supabase.auth.getUser();
  if (error || !user) {
    return new Response(JSON.stringify({ error: "Unauthorized" }), {
      status: 401,
    });
  }

  // Get user profile
  const { data: profile } = await supabase
    .from("profiles")
    .select("name, companion_name")
    .eq("id", user.id)
    .single();

  // Create LiveKit room token
  const roomName = `koi-${user.id}-${Date.now()}`;
  const token = new AccessToken(
    Deno.env.get("LIVEKIT_API_KEY")!,
    Deno.env.get("LIVEKIT_API_SECRET")!,
    {
      identity: user.id,
      name: profile?.name || "User",
      metadata: JSON.stringify({
        user_id: user.id,
        user_name: profile?.name,
        companion_name: profile?.companion_name,
      }),
    }
  );

  token.addGrant({
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canSubscribe: true,
  });

  // Create conversation record
  const { data: conversation } = await supabase
    .from("conversations")
    .insert({ user_id: user.id })
    .select()
    .single();

  return new Response(
    JSON.stringify({
      token: await token.toJwt(),
      url: Deno.env.get("LIVEKIT_URL"),
      roomName,
      conversationId: conversation?.id,
    }),
    { headers: { "Content-Type": "application/json" } }
  );
});
```

**4. Edge Function: delete-user-data**
```typescript
// Handles "delete my data" requests
// Deletes: messages → conversations → memories (Pinecone) → profile
// Must cascade properly
```

#### Supabase Dashboard Config
```
Settings to configure:

1. Auth → Providers → Phone → Enable
2. Auth → Rate Limits → Set to 5/hour per phone
3. Database → Tables → Run SQL above
4. Edge Functions → Deploy generate-room-token
5. Edge Functions → Set secrets:
   - LIVEKIT_API_KEY
   - LIVEKIT_API_SECRET
   - LIVEKIT_URL
```

#### Success Criteria
- [ ] Can create user via phone OTP
- [ ] Profile auto-created on signup
- [ ] Room token generation works
- [ ] RLS policies prevent cross-user access
- [ ] Data deletion cascade works

---

### WORKSTREAM 4: Documentation & Privacy
**Location:** `~/koi-app/docs/`
**Language:** Markdown
**Dependencies:** None

#### Files to Create

**`PRIVACY_POLICY.md`** - User-facing privacy policy:
- Written in plain language (not legalese)
- Explains: what data we collect, why, how long we keep it
- Voice recordings: processed in real-time, NOT stored long-term
- Conversation text: stored for memory feature, user can delete anytime
- Third parties: Sarvam AI processes voice (mention this)
- User rights: view data, delete data, export data
- Contact: email for privacy questions

**`TERMS_OF_SERVICE.md`** - Terms of use:
- Koi is not a medical/mental health professional
- Not a replacement for human relationships
- Disclaimer for advice given
- Age restriction (13+)
- Acceptable use policy

**`SETUP_GUIDE.md`** - Developer setup:
- Complete environment setup for macOS
- Account creation walkthrough with screenshots
- Common errors and solutions
- How to run each component

**`TROUBLESHOOTING.md`** - Common issues:
- "Agent not responding" → check agent logs
- "No audio" → check microphone permissions
- "Connection failed" → check LiveKit URL
- "OTP not received" → check Supabase phone auth config
- Each issue: symptoms, cause, solution

---

## Integration Points (Contracts Between Workstreams)

### Mobile App ↔ Supabase

```typescript
// Auth
supabase.auth.signInWithOtp({ phone: '+91XXXXXXXXXX' })
supabase.auth.verifyOtp({ phone, token, type: 'sms' })

// Profile
supabase.from('profiles').select('*').eq('id', userId).single()
supabase.from('profiles').update({ name, companion_name }).eq('id', userId)

// Room Token
supabase.functions.invoke('generate-room-token')
// Returns: { token: string, url: string, roomName: string, conversationId: string }

// Conversations
supabase.from('conversations').select('*').eq('user_id', userId).order('started_at', { ascending: false })

// Delete Data
supabase.functions.invoke('delete-user-data')
```

### Mobile App ↔ LiveKit

```typescript
// Connect to room
<LiveKitRoom serverUrl={url} token={token} connect={true} audio={true} video={false}>
  <RoomContent />
</LiveKitRoom>

// Track events to detect speaking state
room.on('trackSubscribed', track => { /* agent started speaking */ })
room.on('activeSpeakersChanged', speakers => { /* update VoiceOrb state */ })
```

### Voice Agent ↔ Supabase DB

```python
# Agent reads user data via direct PostgreSQL connection
# Connection string from SUPABASE_DB_URL env var

user = await db.fetchrow("SELECT * FROM profiles WHERE id = $1", user_id)
await db.execute("INSERT INTO messages (conversation_id, user_id, role, content) VALUES ($1, $2, $3, $4)", ...)
```

### Voice Agent ↔ Pinecone

```python
# Store memory
index.upsert(vectors=[{
    "id": f"{user_id}_{timestamp}",
    "values": embedding,
    "metadata": {"user_id": user_id, "summary": "...", "date": "...", "topic": "..."}
}])

# Retrieve memory
results = index.query(
    vector=query_embedding,
    filter={"user_id": user_id},
    top_k=5,
    include_metadata=True
)
```

---

## Environment Variables (All Workstreams)

```bash
# ~/koi-app/.env

# Sarvam AI
SARVAM_API_KEY=

# LiveKit
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
LIVEKIT_URL=wss://your-project.livekit.cloud

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=
SUPABASE_DB_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# Pinecone
PINECONE_API_KEY=
PINECONE_INDEX=koi-memories
```

---

## Execution Order

```
PHASE 0 (Day 1): Account setup + environment
  No agents needed, manual browser work

PHASE 1 (Days 2-5): Parallel agent execution
  ┌─────────────────────────────────────────────────────────┐
  │                                                         │
  │  Agent A: Voice Agent (Python)     ←── CRITICAL PATH    │
  │  Agent B: Mobile App (Expo)                             │
  │  Agent C: Supabase Backend                              │
  │  Agent D: Documentation                                 │
  │                                                         │
  │  All can start simultaneously                           │
  └─────────────────────────────────────────────────────────┘

PHASE 2 (Days 6-8): Integration
  ┌─────────────────────────────────────────────────────────┐
  │                                                         │
  │  Connect Mobile App → Supabase (auth + data)            │
  │  Connect Mobile App → LiveKit → Voice Agent             │
  │  Connect Voice Agent → Supabase DB + Pinecone           │
  │                                                         │
  │  Requires all workstreams to be at baseline             │
  └─────────────────────────────────────────────────────────┘

PHASE 3 (Days 9-12): Polish + Memory
  ┌─────────────────────────────────────────────────────────┐
  │                                                         │
  │  Memory system integration                              │
  │  VoiceOrb animations                                    │
  │  Error handling everywhere                              │
  │  Privacy controls                                       │
  │  Conversation history UI                                │
  │                                                         │
  └─────────────────────────────────────────────────────────┘

PHASE 4 (Days 13-16): Testing + Beta
  ┌─────────────────────────────────────────────────────────┐
  │                                                         │
  │  TestFlight build                                       │
  │  Beta testing (20 users)                                │
  │  Bug fixes                                              │
  │  Performance optimization                               │
  │                                                         │
  └─────────────────────────────────────────────────────────┘
```

---

## Quality Checklist (Must Pass Before Beta)

### Voice
- [ ] End-to-end latency < 3 seconds
- [ ] Natural Hinglish voice quality
- [ ] Interruption handling works
- [ ] No echo/feedback
- [ ] Works on 4G network
- [ ] 5-minute conversation without crash

### App
- [ ] 60fps animations on VoiceOrb
- [ ] No layout jumps on any screen
- [ ] Works on iPhone SE through iPhone 15 Pro Max
- [ ] Dark mode polished
- [ ] Haptic feedback on interactions
- [ ] Microphone permission request is clear
- [ ] Error states are graceful (not crash/blank)
- [ ] Loading states for all async operations

### Backend
- [ ] Phone OTP auth works reliably
- [ ] RLS prevents cross-user data access
- [ ] Room token generation < 500ms
- [ ] Conversations are stored correctly
- [ ] Data deletion works completely

### Privacy
- [ ] Consent shown before first conversation
- [ ] "Delete my data" works
- [ ] Privacy policy accessible from app
- [ ] No sensitive data in logs

---

## First Action: Set Up Accounts

Before any agents start coding, you need to create accounts and get API keys. Here's the exact sequence:

1. **Sarvam AI** → https://www.sarvam.ai → Sign up → Developer → Get API key
2. **LiveKit** → https://cloud.livekit.io → Create project → Copy API Key + Secret + URL
3. **Supabase** → https://supabase.com → New project (region: Mumbai) → Copy URL + anon key + service key + DB URL
4. **Pinecone** → https://www.pinecone.io → Create index "koi-memories" (1024 dims, cosine) → Get API key

Once you have all keys, save them to `~/koi-app/.env` and we launch all 4 workstreams.

---

## Software Engineering Practices

### Git Workflow

**Branching Strategy: GitLab Flow**
```
main              ← production-ready, protected
  └── develop     ← integration branch, CI runs here
       ├── feat/voice-agent       (Workstream 1)
       ├── feat/mobile-app        (Workstream 2)
       ├── feat/supabase-backend  (Workstream 3)
       └── feat/docs-privacy      (Workstream 4)
```

**Rules:**
- `main` is protected — merge only via MR with passing CI
- `develop` is the integration branch — all feature branches merge here first
- Each workstream gets its own feature branch
- Merge requests require at least lint + unit tests passing
- Commit messages follow Conventional Commits: `feat:`, `fix:`, `test:`, `docs:`, `ci:`

**Commit Message Format:**
```
feat(agent): add Sarvam STT integration with retry logic
fix(mobile): resolve VoiceOrb animation jank on iPhone SE
test(supabase): add RLS policy unit tests
docs: update FORPREETAM.md with LiveKit lessons
ci: add Python linting stage to pipeline
```

### Code Quality Standards

**Python (Voice Agent):**
- Formatter: `black` (line length 100)
- Linter: `ruff` (replaces flake8, faster)
- Type checker: `mypy` (strict mode on new files)
- Import sorting: `isort`
- All async functions must have proper error handling and timeouts
- No bare `except:` — always catch specific exceptions

**TypeScript (Mobile App + Edge Functions):**
- Formatter: `prettier`
- Linter: `eslint` with `@typescript-eslint`
- Strict TypeScript: `"strict": true` in tsconfig
- No `any` types — use `unknown` + type guards
- All API calls wrapped in try/catch with user-facing error messages

**SQL (Supabase):**
- All tables have RLS enabled — no exceptions
- All queries use parameterized inputs — no string concatenation
- Indexes on every foreign key and frequently queried column
- Migration files numbered sequentially: `001_`, `002_`, etc.

### Code Review Checklist (for MRs)

Every merge request must pass this checklist:

```
□ Code compiles/runs without errors
□ All existing tests pass
□ New code has tests (unit at minimum)
□ No hardcoded secrets, URLs, or API keys
□ Error handling covers failure cases
□ No console.log/print statements left in (use proper logging)
□ TypeScript: no 'any' types introduced
□ Python: passes black + ruff + mypy
□ Database changes have a migration file
□ Breaking changes documented in MR description
```

---

## WORKSTREAM 5: Testing & Quality (NEW)

**Runs alongside all other workstreams — not blocking, but enforcing quality.**
**Language:** Python + TypeScript + YAML
**Dependencies:** Needs skeleton code from Workstreams 1-3 to write tests against

This workstream is responsible for:
1. Setting up test infrastructure for all components
2. Writing test scaffolds and fixtures
3. Configuring CI/CD pipeline
4. Enforcing coverage thresholds
5. Creating pre-commit hooks

### Test Infrastructure

#### Python Agent Tests (`agent/tests/`)

```
agent/tests/
├── conftest.py                 # Shared fixtures (mock DB, mock Sarvam, mock Pinecone)
├── unit/
│   ├── test_sarvam_stt.py      # STT class: transcription, error handling, retries
│   ├── test_sarvam_llm.py      # LLM class: streaming, token limits, timeouts
│   ├── test_sarvam_tts.py      # TTS class: audio encoding, chunking, empty text
│   ├── test_prompts.py         # Prompt builder: context assembly, token budget
│   ├── test_memory.py          # Memory: retrieval, storage, embedding
│   └── test_db_client.py       # DB client: CRUD operations, connection handling
├── integration/
│   ├── test_voice_pipeline.py  # Full STT → LLM → TTS pipeline with mocked APIs
│   ├── test_memory_flow.py     # Store conversation → retrieve relevant memories
│   └── test_agent_lifecycle.py # Agent connect → converse → disconnect
└── fixtures/
    ├── audio_samples/          # Short audio clips for STT tests
    ├── mock_responses.py       # Canned Sarvam API responses
    └── mock_pinecone.py        # Fake Pinecone index
```

**Key testing patterns:**

```python
# agent/tests/conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_sarvam_client():
    """Mock all Sarvam API calls"""
    client = AsyncMock()
    client.transcribe.return_value = {"transcript": "Yaar, aaj bahut boring tha", "language": "hi-en"}
    client.generate.return_value = "Achha, kya hua? Bata na"
    client.synthesize.return_value = b"fake_audio_pcm_bytes"
    return client

@pytest.fixture
def mock_pinecone():
    """Mock Pinecone vector DB"""
    index = MagicMock()
    index.query.return_value = {"matches": [
        {"id": "mem_1", "score": 0.92, "metadata": {"summary": "Talked about job stress", "date": "2025-02-01"}}
    ]}
    index.upsert.return_value = {"upserted_count": 1}
    return index

@pytest.fixture
def mock_db():
    """Mock asyncpg database pool"""
    pool = AsyncMock()
    conn = AsyncMock()
    conn.fetchrow.return_value = {"id": "user_1", "name": "Rahul", "companion_name": "Koi", "relationship_stage": "familiar"}
    pool.acquire.return_value.__aenter__.return_value = conn
    pool.acquire.return_value.__aexit__.return_value = None
    return pool

@pytest.fixture
def user_context():
    """Standard user context for tests"""
    return {
        "user_id": "user_1",
        "name": "Rahul",
        "companion_name": "Koi",
        "relationship_stage": "familiar",
        "memories": ["Discussed job interview last week", "Sister's wedding coming up"]
    }
```

**Coverage targets:**
- Unit tests: **80%+** on `services/`, `persona/`, `memory/`, `db/`
- Integration tests: **60%+** on pipeline flows
- Overall: **75%+**
- Fail CI if coverage drops below threshold

**pytest configuration:**
```toml
# In pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
markers = [
    "unit: unit tests (fast, no external deps)",
    "integration: integration tests (may use mocked external services)",
    "slow: tests that take >5 seconds"
]

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/__init__.py"]

[tool.coverage.report]
fail_under = 75
show_missing = true
```

#### Mobile App Tests (`mobile/KoiApp/__tests__/`)

```
mobile/KoiApp/__tests__/
├── setup.ts                        # Global test setup, mocks
├── unit/
│   ├── components/
│   │   ├── VoiceOrb.test.tsx       # Animation states, transitions
│   │   ├── TranscriptBubble.test.tsx
│   │   ├── CallControls.test.tsx   # Button states, callbacks
│   │   └── ConsentModal.test.tsx   # Consent flow, persistence
│   ├── screens/
│   │   ├── OnboardingScreen.test.tsx  # OTP flow, validation
│   │   ├── HomeScreen.test.tsx        # Navigation, recent convos
│   │   ├── ConversationScreen.test.tsx # LiveKit connect, states
│   │   └── SettingsScreen.test.tsx    # Profile edit, delete data
│   ├── stores/
│   │   ├── authStore.test.ts       # Auth state transitions
│   │   └── settingsStore.test.ts   # Preference persistence
│   └── services/
│       ├── supabase.test.ts        # API call mocking
│       └── livekit.test.ts         # Room token, connection
└── integration/
    ├── auth-flow.test.tsx          # Full onboarding → home
    └── conversation-flow.test.tsx  # Start call → talk → end
```

**Testing approach:**
- Use React Native Testing Library (not Enzyme — it's deprecated)
- Test user behavior, not implementation details
- Mock Supabase client globally in `setup.ts`
- Mock LiveKit room/tracks at the module level
- Snapshot tests only for static layouts (not for dynamic content)

**Coverage targets:**
- Components: **70%+**
- Stores: **90%+** (pure logic, easy to test)
- Services: **80%+**
- Screens: **60%+** (harder to test, more integration-like)
- Overall: **70%+**

**Jest configuration:**
```javascript
// jest.config.js
module.exports = {
  preset: 'jest-expo',
  setupFilesAfterSetup: ['<rootDir>/__tests__/setup.ts'],
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/index.ts',
    '!src/theme/**',       // static config, not worth testing
  ],
  coverageThreshold: {
    global: {
      branches: 60,
      functions: 70,
      lines: 70,
      statements: 70
    }
  },
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@unimodules/.*|unimodules|sentry-expo|native-base|react-native-svg|@livekit/.*))'
  ]
};
```

#### Supabase Edge Function Tests (`supabase/tests/`)

```
supabase/tests/
├── generate-room-token.test.ts     # Token generation, auth verification
├── delete-user-data.test.ts        # Cascade deletion, Pinecone cleanup
└── mocks/
    ├── supabase-client.ts          # Mock Supabase client factory
    └── livekit-sdk.ts              # Mock AccessToken generation
```

**Testing approach:**
- Use Deno.test (built-in, no extra deps)
- Extract handler logic from `serve()` wrapper for testability
- Mock Supabase client and LiveKit SDK
- Test auth rejection, happy path, and error cases

**Coverage target:** **60%+**

### Pre-commit Hooks

Install via `husky` (mobile/node) and `pre-commit` (agent/python):

```yaml
# agent/.pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.2.0
    hooks:
      - id: black
        args: [--line-length=100]
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
        args: [--ignore-missing-imports]
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-added-large-files
        args: [--maxkb=500]
      - id: check-yaml
      - id: end-of-file-fixer
      - id: trailing-whitespace
      - id: no-commit-to-branch
        args: [--branch, main]
```

### Logging Standards

**Python Agent:**
```python
import logging
logger = logging.getLogger("koi.agent")

# Structured logging format
logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)s [%(user_id)s] %(message)s',
    level=logging.INFO
)

# Usage:
logger.info("STT transcription complete", extra={"user_id": user_id, "latency_ms": 450})
logger.error("Sarvam API timeout", extra={"user_id": user_id, "endpoint": "/speech-to-text"})
```

**Mobile App:**
```typescript
// No console.log in production — use a logger that can be disabled
const logger = {
  info: (msg: string, data?: Record<string, unknown>) => {
    if (__DEV__) console.log(`[KOI] ${msg}`, data);
  },
  error: (msg: string, error?: Error) => {
    if (__DEV__) console.error(`[KOI] ${msg}`, error);
    // In production: send to crash reporting (Sentry/Bugsnag)
  }
};
```

**Rule:** Never log user conversation content in production. Log metadata only (latencies, error types, user IDs).

### Error Handling Standards

**Python Agent — Retry with backoff:**
```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=0.5, max=5))
async def call_sarvam_api(endpoint: str, payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(f"{SARVAM_BASE}/{endpoint}", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
```

**Mobile App — User-facing errors:**
```typescript
// Every API call wrapped with user-friendly error handling
async function startConversation(): Promise<RoomToken> {
  try {
    const { data, error } = await supabase.functions.invoke('generate-room-token');
    if (error) throw error;
    return data;
  } catch (err) {
    // Never show raw error to user
    throw new AppError(
      'Unable to start conversation. Please check your connection and try again.',
      err
    );
  }
}
```

### Dependency Management

**Python:** Use `poetry` with locked dependencies (`poetry.lock` committed to git)
**Node:** Use `pnpm` with locked dependencies (`pnpm-lock.yaml` committed to git)
**Deno:** Import map in `deno.json` with pinned versions

**Security scanning:** CI pipeline runs `npm audit` and `pip audit` on every MR.

---

## WORKSTREAM 6: CI/CD & GitLab (NEW)

**Location:** `~/koi-app/` (root-level config files)
**Language:** YAML + Shell
**Dependencies:** None (can set up independently)

### GitLab Repository Setup

1. Create private repo on GitLab: `koi-app`
2. Add remote: `git remote add origin git@gitlab.com:YOUR_USERNAME/koi-app.git`
3. Push initial structure: `git push -u origin main`
4. Protect `main` branch: Settings → Repository → Protected Branches
5. Set CI/CD variables: Settings → CI/CD → Variables:
   - `SARVAM_API_KEY` (masked)
   - `LIVEKIT_API_KEY` (masked)
   - `LIVEKIT_API_SECRET` (masked)
   - `LIVEKIT_URL`
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY` (masked)
   - `SUPABASE_SERVICE_KEY` (masked)
   - `SUPABASE_DB_URL` (masked)
   - `PINECONE_API_KEY` (masked)

### Pipeline Overview

```
Every push/MR triggers:

  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────────┐
  │  LINT   │ →  │  TEST   │ →  │  BUILD  │ →  │  DEPLOY  │
  └─────────┘    └─────────┘    └─────────┘    └──────────┘

  Lint:                Test:               Build:              Deploy:
  - black (py)         - pytest unit       - Docker agent      - Staging (auto)
  - ruff (py)          - pytest integ      - Expo iOS build    - Production (manual)
  - mypy (py)          - jest unit         - Expo Android
  - eslint (ts)        - jest integ
  - prettier (ts)      - deno test
  - deno fmt/lint      - coverage check
```

**Conditional execution:** Each stage only runs if relevant files changed (e.g., Python lint only runs if `agent/**` changed).

### Pipeline Stages

See `.gitlab-ci.yml` in the repository root for the full configuration.

### Success Criteria
- [ ] CI pipeline runs on every push
- [ ] Lint stage catches formatting issues
- [ ] Test stage reports coverage in MR widget
- [ ] Coverage thresholds enforced (fail if below)
- [ ] Docker build succeeds for voice agent
- [ ] Protected branch prevents direct push to main
- [ ] CI/CD variables configured (not in code)

---

## Updated Execution Order (with Testing + CI/CD)

```
PHASE 0 (Day 1): Account setup + environment + GitLab repo
  Manual: Create accounts, get API keys, create GitLab repo

PHASE 1 (Days 2-5): Parallel agent execution (6 workstreams)
  ┌─────────────────────────────────────────────────────────┐
  │                                                         │
  │  Agent A: Voice Agent (Python)     ←── CRITICAL PATH    │
  │  Agent B: Mobile App (Expo)                             │
  │  Agent C: Supabase Backend                              │
  │  Agent D: Documentation & Privacy                       │
  │  Agent E: Testing & Quality        ←── NEW              │
  │  Agent F: CI/CD & GitLab           ←── NEW              │
  │                                                         │
  │  All can start simultaneously                           │
  └─────────────────────────────────────────────────────────┘

PHASE 2 (Days 6-8): Integration + Test Coverage
  ┌─────────────────────────────────────────────────────────┐
  │                                                         │
  │  Connect Mobile App → Supabase (auth + data)            │
  │  Connect Mobile App → LiveKit → Voice Agent             │
  │  Connect Voice Agent → Supabase DB + Pinecone           │
  │  Write integration tests for all connections            │
  │  CI pipeline green on develop branch                    │
  │                                                         │
  └─────────────────────────────────────────────────────────┘

PHASE 3 (Days 9-12): Polish + Memory + Coverage Gates
  ┌─────────────────────────────────────────────────────────┐
  │                                                         │
  │  Memory system integration                              │
  │  VoiceOrb animations                                    │
  │  Error handling everywhere                              │
  │  Privacy controls                                       │
  │  Conversation history UI                                │
  │  Coverage thresholds enforced in CI                     │
  │  All MRs require passing pipeline                       │
  │                                                         │
  └─────────────────────────────────────────────────────────┘

PHASE 4 (Days 13-16): Testing + Beta
  ┌─────────────────────────────────────────────────────────┐
  │                                                         │
  │  TestFlight build via CI pipeline                       │
  │  Beta testing (20 users)                                │
  │  Bug fixes with regression tests                       │
  │  Performance profiling + optimization                   │
  │  Final coverage report                                  │
  │                                                         │
  └─────────────────────────────────────────────────────────┘
```

---

## Updated Quality Checklist (Must Pass Before Beta)

### Voice
- [ ] End-to-end latency < 3 seconds
- [ ] Natural Hinglish voice quality
- [ ] Interruption handling works
- [ ] No echo/feedback
- [ ] Works on 4G network
- [ ] 5-minute conversation without crash

### App
- [ ] 60fps animations on VoiceOrb
- [ ] No layout jumps on any screen
- [ ] Works on iPhone SE through iPhone 15 Pro Max
- [ ] Dark mode polished
- [ ] Haptic feedback on interactions
- [ ] Microphone permission request is clear
- [ ] Error states are graceful (not crash/blank)
- [ ] Loading states for all async operations

### Backend
- [ ] Phone OTP auth works reliably
- [ ] RLS prevents cross-user data access
- [ ] Room token generation < 500ms
- [ ] Conversations are stored correctly
- [ ] Data deletion works completely

### Privacy
- [ ] Consent shown before first conversation
- [ ] "Delete my data" works
- [ ] Privacy policy accessible from app
- [ ] No sensitive data in logs

### Testing (NEW)
- [ ] Python agent: 75%+ code coverage
- [ ] Mobile app: 70%+ code coverage
- [ ] Supabase functions: 60%+ code coverage
- [ ] All tests pass on CI (no skipped tests)
- [ ] Integration tests cover all cross-service boundaries
- [ ] No flaky tests (run 3x, pass 3x)

### Engineering (NEW)
- [ ] CI pipeline green on main branch
- [ ] All code passes lint (no warnings)
- [ ] No hardcoded secrets in codebase
- [ ] Structured logging in all services
- [ ] Error handling on all external API calls
- [ ] Retry logic on Sarvam API calls
- [ ] Conventional commit messages throughout
- [ ] All dependencies version-locked
