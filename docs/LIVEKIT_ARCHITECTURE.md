# LiveKit Voice Agent Architecture
# Koi - Real-Time Voice Companion

**Version:** 2.0
**Date:** February 2025
**Approach:** Native App + LiveKit Real-Time Voice

---

## 1. Why LiveKit Changes Everything

### Voice Notes vs Real-Time Voice

| Aspect | Voice Notes (WhatsApp) | Real-Time Voice (LiveKit) |
|--------|------------------------|---------------------------|
| **Latency** | 3-5 seconds | 300-500ms |
| **Feel** | Async messaging | Real conversation |
| **Interruption** | Can't interrupt | Natural back-and-forth |
| **Emotion** | Delayed reaction | Immediate response |
| **Intimacy** | Medium | Very high |
| **Complexity** | Low | High |

**The key insight:** With LiveKit, talking to Koi feels like talking to a friend on a phone call, not exchanging voice messages.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         KOI REAL-TIME VOICE ARCHITECTURE                     │
└─────────────────────────────────────────────────────────────────────────────┘

                              ┌─────────────────┐
                              │   MOBILE APP    │
                              │  (React Native) │
                              │                 │
                              │  • Audio capture│
                              │  • Audio playback│
                              │  • LiveKit SDK  │
                              │  • UI/UX        │
                              └────────┬────────┘
                                       │
                                       │ WebRTC
                                       │
                              ┌────────▼────────┐
                              │   LIVEKIT       │
                              │   CLOUD         │
                              │                 │
                              │  • Media routing│
                              │  • Room mgmt    │
                              │  • Low latency  │
                              └────────┬────────┘
                                       │
                                       │ WebSocket
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                            VOICE AGENT SERVER                                │
│                                                                              │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐        │
│   │  LIVEKIT        │    │   SARVAM        │    │   CONVERSATION  │        │
│   │  AGENT          │───▶│   PIPELINE      │───▶│   ENGINE        │        │
│   │                 │    │                 │    │                 │        │
│   │  • Joins room   │    │  • STT stream   │    │  • Memory       │        │
│   │  • Audio stream │    │  • LLM stream   │    │  • Context      │        │
│   │  • Track mgmt   │    │  • TTS stream   │    │  • Persona      │        │
│   └─────────────────┘    └─────────────────┘    └─────────────────┘        │
│                                                                              │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
             ┌──────────┐       ┌──────────┐       ┌──────────┐
             │PostgreSQL│       │ Pinecone │       │  Redis   │
             │          │       │(Memories)│       │ (Cache)  │
             └──────────┘       └──────────┘       └──────────┘
```

---

## 3. Component Deep Dive

### 3.1 Mobile App (React Native)

**Why React Native:**
- Single codebase for iOS + Android
- LiveKit has excellent React Native SDK
- Fast development cycle
- Good performance for audio

**Key Dependencies:**
```json
{
  "dependencies": {
    "@livekit/react-native": "^2.0.0",
    "@livekit/react-native-webrtc": "^1.0.0",
    "react-native": "0.73.x",
    "@react-navigation/native": "^6.x",
    "react-native-reanimated": "^3.x",
    "zustand": "^4.x",
    "@tanstack/react-query": "^5.x",
    "react-native-mmkv": "^2.x"
  }
}
```

**App Structure:**
```
app/
├── src/
│   ├── screens/
│   │   ├── OnboardingScreen.tsx    # First-time setup
│   │   ├── HomeScreen.tsx          # Main conversation screen
│   │   ├── HistoryScreen.tsx       # Past conversations
│   │   ├── SettingsScreen.tsx      # Preferences
│   │   └── ProfileScreen.tsx       # User profile
│   ├── components/
│   │   ├── VoiceOrb.tsx            # Animated speaking indicator
│   │   ├── TranscriptView.tsx      # Live transcription
│   │   ├── MoodIndicator.tsx       # Koi's current mood
│   │   └── CallControls.tsx        # Mute, end call, etc.
│   ├── services/
│   │   ├── livekit.ts              # LiveKit connection
│   │   ├── api.ts                  # Backend API calls
│   │   └── auth.ts                 # Authentication
│   ├── stores/
│   │   ├── userStore.ts            # User state
│   │   ├── conversationStore.ts    # Conversation state
│   │   └── settingsStore.ts        # App settings
│   └── utils/
│       ├── audio.ts                # Audio utilities
│       └── haptics.ts              # Haptic feedback
├── App.tsx
└── index.js
```

### 3.2 LiveKit Voice Agent (Python)

**Why Python:**
- Sarvam has Python SDK
- LiveKit Agents framework is Python-native
- Easy async handling
- Mature ML/AI ecosystem

**Agent Structure:**
```
agent/
├── src/
│   ├── main.py                     # Entry point
│   ├── agent.py                    # Voice agent logic
│   ├── pipeline.py                 # STT → LLM → TTS pipeline
│   ├── memory/
│   │   ├── retriever.py            # Memory retrieval
│   │   └── storage.py              # Memory storage
│   ├── persona/
│   │   ├── prompts.py              # System prompts
│   │   └── personality.py          # Persona logic
│   ├── services/
│   │   ├── sarvam.py               # Sarvam API wrapper
│   │   └── database.py             # PostgreSQL client
│   └── utils/
│       ├── logging.py              # Structured logging
│       └── metrics.py              # Performance metrics
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

### 3.3 Backend API (Node.js/Python)

**Responsibilities:**
- User authentication
- Room token generation
- User profile management
- Conversation history
- Payments/subscriptions

**API Endpoints:**
```
POST /api/v1/auth/signup          # Create account
POST /api/v1/auth/login           # Get JWT token
POST /api/v1/auth/verify-otp      # OTP verification

GET  /api/v1/users/me             # Get user profile
PUT  /api/v1/users/me             # Update profile

POST /api/v1/rooms/create         # Create LiveKit room
POST /api/v1/rooms/token          # Get room access token

GET  /api/v1/conversations        # List past conversations
GET  /api/v1/conversations/:id    # Get conversation details

POST /api/v1/subscriptions        # Create subscription
GET  /api/v1/subscriptions/status # Check subscription status
```

---

## 4. LiveKit + Sarvam Integration

### 4.1 The Voice Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REAL-TIME VOICE PIPELINE                             │
└─────────────────────────────────────────────────────────────────────────────┘

User speaks → Audio chunks stream in real-time
                    │
                    ▼
        ┌───────────────────────┐
        │   VOICE ACTIVITY      │
        │   DETECTION (VAD)     │
        │                       │
        │   Detects when user   │
        │   starts/stops talking│
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   SARVAM STT          │
        │   (Streaming)         │
        │                       │
        │   • Audio → Text      │
        │   • Real-time partial │
        │   • Final transcript  │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   CONTEXT ASSEMBLY    │
        │                       │
        │   • User profile      │
        │   • Memory retrieval  │
        │   • Conversation hist │
        │   • Build prompt      │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   SARVAM LLM          │
        │   (Streaming)         │
        │                       │
        │   • Stream tokens     │
        │   • Sentence detection│
        │   • Interruptible     │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   SARVAM TTS          │
        │   (Streaming)         │
        │                       │
        │   • Text → Audio      │
        │   • Sentence by sent  │
        │   • Low latency       │
        └───────────┬───────────┘
                    │
                    ▼
        Audio streams back to user in real-time
```

### 4.2 Python Agent Implementation

```python
# agent/src/agent.py

import asyncio
from livekit import agents, rtc
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice_assistant import VoiceAssistant
from livekit.plugins import silero

from pipeline import SarvamPipeline
from memory.retriever import MemoryRetriever
from persona.prompts import build_system_prompt
from services.database import DatabaseService

class KoiVoiceAgent:
    def __init__(self, ctx: JobContext):
        self.ctx = ctx
        self.room = ctx.room
        self.db = DatabaseService()
        self.memory = MemoryRetriever()

    async def start(self):
        # Get user info from room metadata
        user_id = self.room.metadata.get("user_id")
        user = await self.db.get_user(user_id)

        # Build persona context
        memories = await self.memory.retrieve_relevant(user_id, limit=5)
        system_prompt = build_system_prompt(user, memories)

        # Create Sarvam-powered pipeline
        pipeline = SarvamPipeline(
            system_prompt=system_prompt,
            user_id=user_id,
            language="hi-IN"
        )

        # Create voice assistant
        assistant = VoiceAssistant(
            vad=silero.VAD.load(),  # Voice Activity Detection
            stt=pipeline.stt,
            llm=pipeline.llm,
            tts=pipeline.tts,
            chat_ctx=pipeline.chat_context,
            allow_interruptions=True,
            interrupt_speech_duration=0.5,
            min_endpointing_delay=0.5,
        )

        # Start the assistant
        assistant.start(self.room)

        # Handle events
        @assistant.on("user_speech_committed")
        async def on_user_speech(text: str):
            # Store user message
            await self.db.store_message(user_id, "user", text)
            # Update memory asynchronously
            asyncio.create_task(self.memory.process_message(user_id, text))

        @assistant.on("agent_speech_committed")
        async def on_agent_speech(text: str):
            # Store agent message
            await self.db.store_message(user_id, "assistant", text)

        # Initial greeting
        await assistant.say(
            f"Hey {user.name}! Kaisa chal raha hai?",
            allow_interruptions=True
        )


async def entrypoint(ctx: JobContext):
    agent = KoiVoiceAgent(ctx)
    await agent.start()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```

### 4.3 Sarvam Pipeline Implementation

```python
# agent/src/pipeline.py

import os
from dataclasses import dataclass
from typing import AsyncIterable
import httpx

from livekit.agents import llm, stt, tts


class SarvamSTT(stt.STT):
    """Sarvam Speech-to-Text with streaming support"""

    def __init__(self, language: str = "hi-IN"):
        super().__init__(streaming_supported=True)
        self.api_key = os.environ["SARVAM_API_KEY"]
        self.base_url = "https://api.sarvam.ai/v1"
        self.language = language

    async def recognize(
        self,
        buffer: AudioBuffer,
        *,
        language: str | None = None,
    ) -> stt.SpeechEvent:
        # Non-streaming recognition
        async with httpx.AsyncClient() as client:
            files = {"file": ("audio.wav", buffer.to_wav(), "audio/wav")}
            data = {
                "model": "saarika:v2.5",
                "language_code": language or self.language
            }
            response = await client.post(
                f"{self.base_url}/speech-to-text",
                files=files,
                data=data,
                headers={"api-subscription-key": self.api_key}
            )
            result = response.json()
            return stt.SpeechEvent(
                type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                alternatives=[stt.SpeechData(text=result["transcript"])]
            )

    def stream(self, *, language: str | None = None) -> "SarvamSTTStream":
        return SarvamSTTStream(self, language or self.language)


class SarvamSTTStream(stt.SpeechStream):
    """Streaming STT using Sarvam's WebSocket API"""

    def __init__(self, stt_instance: SarvamSTT, language: str):
        super().__init__()
        self.stt = stt_instance
        self.language = language
        self._ws = None

    async def _run(self):
        import websockets

        url = f"wss://api.sarvam.ai/v1/speech-to-text/stream"
        headers = {"api-subscription-key": self.stt.api_key}

        async with websockets.connect(url, extra_headers=headers) as ws:
            self._ws = ws

            # Send config
            await ws.send(json.dumps({
                "model": "saarika:v2.5",
                "language_code": self.language,
                "encoding": "linear16",
                "sample_rate": 16000
            }))

            # Handle incoming transcripts
            async for message in ws:
                data = json.loads(message)
                if data.get("transcript"):
                    event_type = (
                        stt.SpeechEventType.FINAL_TRANSCRIPT
                        if data.get("is_final")
                        else stt.SpeechEventType.INTERIM_TRANSCRIPT
                    )
                    self._event_ch.send_nowait(stt.SpeechEvent(
                        type=event_type,
                        alternatives=[stt.SpeechData(text=data["transcript"])]
                    ))

    async def push_frame(self, frame: rtc.AudioFrame):
        if self._ws:
            await self._ws.send(frame.data.tobytes())


class SarvamLLM(llm.LLM):
    """Sarvam LLM with streaming support"""

    def __init__(self):
        super().__init__()
        self.api_key = os.environ["SARVAM_API_KEY"]
        self.base_url = "https://api.sarvam.ai/v1"

    async def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        fnc_ctx: llm.FunctionContext | None = None,
        temperature: float = 0.8,
        n: int = 1,
    ) -> "SarvamLLMStream":
        return SarvamLLMStream(self, chat_ctx, temperature)


class SarvamLLMStream(llm.LLMStream):
    """Streaming LLM responses from Sarvam"""

    def __init__(self, llm_instance: SarvamLLM, chat_ctx: llm.ChatContext, temperature: float):
        super().__init__(chat_ctx=chat_ctx, fnc_ctx=None)
        self.llm = llm_instance
        self.temperature = temperature

    async def _run(self):
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in self._chat_ctx.messages
        ]

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.llm.base_url}/chat/completions",
                json={
                    "model": "sarvam-m",
                    "messages": messages,
                    "temperature": self.temperature,
                    "stream": True
                },
                headers={
                    "api-subscription-key": self.llm.api_key,
                    "Content-Type": "application/json"
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        if content := data.get("choices", [{}])[0].get("delta", {}).get("content"):
                            self._event_ch.send_nowait(llm.ChatChunk(
                                choices=[llm.Choice(
                                    delta=llm.ChoiceDelta(content=content)
                                )]
                            ))


class SarvamTTS(tts.TTS):
    """Sarvam Text-to-Speech with streaming support"""

    def __init__(self, voice: str = "meera", language: str = "hi-IN"):
        super().__init__(streaming_supported=True)
        self.api_key = os.environ["SARVAM_API_KEY"]
        self.base_url = "https://api.sarvam.ai/v1"
        self.voice = voice
        self.language = language

    def synthesize(self, text: str) -> "SarvamTTSStream":
        return SarvamTTSStream(self, text)


class SarvamTTSStream(tts.SynthesizeStream):
    """Streaming TTS from Sarvam"""

    def __init__(self, tts_instance: SarvamTTS, text: str):
        super().__init__()
        self.tts = tts_instance
        self.text = text

    async def _run(self):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.tts.base_url}/text-to-speech",
                json={
                    "text": self.text,
                    "model": "bulbul:v3",
                    "target_language_code": self.tts.language,
                    "speaker": self.tts.voice,
                    "enable_preprocessing": True
                },
                headers={
                    "api-subscription-key": self.tts.api_key,
                    "Content-Type": "application/json"
                }
            )

            result = response.json()

            # Convert base64 audio to frames and send
            import base64
            audio_data = base64.b64decode(result["audio_base64"])

            # Send audio frames
            chunk_size = 960  # 20ms at 24kHz
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i+chunk_size]
                frame = rtc.AudioFrame(
                    data=chunk,
                    sample_rate=24000,
                    num_channels=1,
                    samples_per_channel=len(chunk) // 2
                )
                self._event_ch.send_nowait(tts.SynthesizedAudio(frame=frame))


@dataclass
class SarvamPipeline:
    """Complete Sarvam-powered voice pipeline"""

    system_prompt: str
    user_id: str
    language: str = "hi-IN"
    voice: str = "meera"

    def __post_init__(self):
        self.stt = SarvamSTT(language=self.language)
        self.llm = SarvamLLM()
        self.tts = SarvamTTS(voice=self.voice, language=self.language)

        # Initialize chat context with system prompt
        self.chat_context = llm.ChatContext()
        self.chat_context.messages.append(
            llm.ChatMessage(role="system", content=self.system_prompt)
        )
```

---

## 5. React Native App Implementation

### 5.1 Project Setup

```bash
# Create new React Native project
npx react-native init KoiApp --template react-native-template-typescript

cd KoiApp

# Install dependencies
npm install @livekit/react-native @livekit/react-native-webrtc
npm install @react-navigation/native @react-navigation/native-stack
npm install react-native-screens react-native-safe-area-context
npm install react-native-gesture-handler react-native-reanimated
npm install zustand @tanstack/react-query
npm install react-native-mmkv  # For local storage
npm install react-native-linear-gradient
npm install lottie-react-native  # For animations

# iOS specific
cd ios && pod install && cd ..
```

### 5.2 Core App Structure

```typescript
// src/App.tsx

import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { registerGlobals } from '@livekit/react-native';

// Register LiveKit globals
registerGlobals();

import { OnboardingScreen } from './screens/OnboardingScreen';
import { HomeScreen } from './screens/HomeScreen';
import { ConversationScreen } from './screens/ConversationScreen';
import { SettingsScreen } from './screens/SettingsScreen';

const Stack = createNativeStackNavigator();
const queryClient = new QueryClient();

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <NavigationContainer>
        <Stack.Navigator
          initialRouteName="Home"
          screenOptions={{ headerShown: false }}
        >
          <Stack.Screen name="Onboarding" component={OnboardingScreen} />
          <Stack.Screen name="Home" component={HomeScreen} />
          <Stack.Screen name="Conversation" component={ConversationScreen} />
          <Stack.Screen name="Settings" component={SettingsScreen} />
        </Stack.Navigator>
      </NavigationContainer>
    </QueryClientProvider>
  );
}
```

### 5.3 Conversation Screen (The Magic)

```typescript
// src/screens/ConversationScreen.tsx

import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  StyleSheet,
  TouchableOpacity,
  Text,
  Animated,
} from 'react-native';
import {
  LiveKitRoom,
  useParticipant,
  useRoomContext,
  AudioSession,
  useTracks,
} from '@livekit/react-native';
import { Track } from 'livekit-client';
import LinearGradient from 'react-native-linear-gradient';

import { VoiceOrb } from '../components/VoiceOrb';
import { TranscriptView } from '../components/TranscriptView';
import { useConversationStore } from '../stores/conversationStore';
import { api } from '../services/api';

interface ConversationScreenProps {
  navigation: any;
}

export function ConversationScreen({ navigation }: ConversationScreenProps) {
  const [roomToken, setRoomToken] = useState<string | null>(null);
  const [roomUrl, setRoomUrl] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(true);

  // Get room token on mount
  useEffect(() => {
    async function connect() {
      try {
        // Start audio session (required for iOS)
        await AudioSession.startAudioSession();

        // Get room token from backend
        const { token, url } = await api.createRoom();
        setRoomToken(token);
        setRoomUrl(url);
        setIsConnecting(false);
      } catch (error) {
        console.error('Failed to connect:', error);
      }
    }

    connect();

    return () => {
      AudioSession.stopAudioSession();
    };
  }, []);

  const handleDisconnect = useCallback(() => {
    navigation.goBack();
  }, [navigation]);

  if (isConnecting || !roomToken || !roomUrl) {
    return (
      <LinearGradient colors={['#1a1a2e', '#16213e']} style={styles.container}>
        <Text style={styles.connectingText}>Connecting to Koi...</Text>
      </LinearGradient>
    );
  }

  return (
    <LiveKitRoom
      serverUrl={roomUrl}
      token={roomToken}
      connect={true}
      audio={true}
      video={false}
    >
      <RoomContent onDisconnect={handleDisconnect} />
    </LiveKitRoom>
  );
}

function RoomContent({ onDisconnect }: { onDisconnect: () => void }) {
  const room = useRoomContext();
  const [isMuted, setIsMuted] = useState(false);
  const [transcript, setTranscript] = useState<string[]>([]);
  const [isKoiSpeaking, setIsKoiSpeaking] = useState(false);

  // Get audio tracks
  const tracks = useTracks([Track.Source.Microphone, Track.Source.Unknown]);

  // Monitor Koi's speaking state
  useEffect(() => {
    const handleTrackSubscribed = (track: any) => {
      if (track.kind === 'audio') {
        setIsKoiSpeaking(true);
      }
    };

    const handleTrackUnsubscribed = () => {
      setIsKoiSpeaking(false);
    };

    room.on('trackSubscribed', handleTrackSubscribed);
    room.on('trackUnsubscribed', handleTrackUnsubscribed);

    return () => {
      room.off('trackSubscribed', handleTrackSubscribed);
      room.off('trackUnsubscribed', handleTrackUnsubscribed);
    };
  }, [room]);

  // Handle data messages (transcripts)
  useEffect(() => {
    const handleDataReceived = (payload: Uint8Array) => {
      const data = JSON.parse(new TextDecoder().decode(payload));
      if (data.type === 'transcript') {
        setTranscript(prev => [...prev, `${data.role}: ${data.text}`]);
      }
    };

    room.on('dataReceived', handleDataReceived);
    return () => room.off('dataReceived', handleDataReceived);
  }, [room]);

  const toggleMute = useCallback(async () => {
    const localParticipant = room.localParticipant;
    await localParticipant.setMicrophoneEnabled(isMuted);
    setIsMuted(!isMuted);
  }, [room, isMuted]);

  const endCall = useCallback(async () => {
    await room.disconnect();
    onDisconnect();
  }, [room, onDisconnect]);

  return (
    <LinearGradient colors={['#1a1a2e', '#16213e']} style={styles.container}>
      {/* Voice Orb - Visual representation of Koi */}
      <View style={styles.orbContainer}>
        <VoiceOrb
          isSpeaking={isKoiSpeaking}
          isListening={!isMuted && !isKoiSpeaking}
        />
        <Text style={styles.koiName}>Koi</Text>
        <Text style={styles.statusText}>
          {isKoiSpeaking ? 'Speaking...' : 'Listening...'}
        </Text>
      </View>

      {/* Live Transcript */}
      <TranscriptView transcript={transcript} />

      {/* Controls */}
      <View style={styles.controls}>
        <TouchableOpacity
          style={[styles.controlButton, isMuted && styles.mutedButton]}
          onPress={toggleMute}
        >
          <Text style={styles.controlIcon}>{isMuted ? '🔇' : '🎤'}</Text>
          <Text style={styles.controlLabel}>{isMuted ? 'Unmute' : 'Mute'}</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.controlButton, styles.endButton]}
          onPress={endCall}
        >
          <Text style={styles.controlIcon}>📞</Text>
          <Text style={styles.controlLabel}>End</Text>
        </TouchableOpacity>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 60,
  },
  connectingText: {
    color: '#fff',
    fontSize: 18,
    marginTop: 'auto',
    marginBottom: 'auto',
  },
  orbContainer: {
    alignItems: 'center',
    marginTop: 40,
  },
  koiName: {
    color: '#fff',
    fontSize: 28,
    fontWeight: '600',
    marginTop: 20,
  },
  statusText: {
    color: '#888',
    fontSize: 16,
    marginTop: 8,
  },
  controls: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 40,
    marginBottom: 40,
  },
  controlButton: {
    alignItems: 'center',
    padding: 16,
    borderRadius: 50,
    backgroundColor: 'rgba(255,255,255,0.1)',
    width: 80,
    height: 80,
    justifyContent: 'center',
  },
  mutedButton: {
    backgroundColor: 'rgba(255,100,100,0.3)',
  },
  endButton: {
    backgroundColor: 'rgba(255,59,48,0.8)',
  },
  controlIcon: {
    fontSize: 24,
  },
  controlLabel: {
    color: '#fff',
    fontSize: 12,
    marginTop: 4,
  },
});
```

### 5.4 Voice Orb Component (The Visual Magic)

```typescript
// src/components/VoiceOrb.tsx

import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated, Easing } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';

interface VoiceOrbProps {
  isSpeaking: boolean;
  isListening: boolean;
}

export function VoiceOrb({ isSpeaking, isListening }: VoiceOrbProps) {
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const opacityAnim = useRef(new Animated.Value(0.5)).current;
  const rotateAnim = useRef(new Animated.Value(0)).current;

  // Pulse animation when speaking
  useEffect(() => {
    if (isSpeaking) {
      Animated.loop(
        Animated.sequence([
          Animated.parallel([
            Animated.timing(scaleAnim, {
              toValue: 1.15,
              duration: 300,
              easing: Easing.out(Easing.ease),
              useNativeDriver: true,
            }),
            Animated.timing(opacityAnim, {
              toValue: 0.8,
              duration: 300,
              useNativeDriver: true,
            }),
          ]),
          Animated.parallel([
            Animated.timing(scaleAnim, {
              toValue: 1,
              duration: 300,
              easing: Easing.in(Easing.ease),
              useNativeDriver: true,
            }),
            Animated.timing(opacityAnim, {
              toValue: 0.5,
              duration: 300,
              useNativeDriver: true,
            }),
          ]),
        ])
      ).start();
    } else {
      scaleAnim.setValue(1);
      opacityAnim.setValue(0.5);
    }
  }, [isSpeaking]);

  // Gentle breathing animation when listening
  useEffect(() => {
    if (isListening && !isSpeaking) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(scaleAnim, {
            toValue: 1.05,
            duration: 2000,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
          Animated.timing(scaleAnim, {
            toValue: 1,
            duration: 2000,
            easing: Easing.inOut(Easing.ease),
            useNativeDriver: true,
          }),
        ])
      ).start();
    }
  }, [isListening, isSpeaking]);

  // Continuous rotation
  useEffect(() => {
    Animated.loop(
      Animated.timing(rotateAnim, {
        toValue: 1,
        duration: 20000,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();
  }, []);

  const rotate = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <View style={styles.container}>
      {/* Outer glow rings */}
      <Animated.View
        style={[
          styles.glowRing,
          styles.outerRing,
          {
            opacity: opacityAnim,
            transform: [{ scale: scaleAnim }, { rotate }],
          },
        ]}
      />
      <Animated.View
        style={[
          styles.glowRing,
          styles.middleRing,
          {
            opacity: Animated.multiply(opacityAnim, 0.7),
            transform: [{ scale: scaleAnim }],
          },
        ]}
      />

      {/* Main orb */}
      <Animated.View
        style={[
          styles.orb,
          { transform: [{ scale: scaleAnim }] },
        ]}
      >
        <LinearGradient
          colors={
            isSpeaking
              ? ['#667eea', '#764ba2']
              : isListening
              ? ['#11998e', '#38ef7d']
              : ['#4a5568', '#2d3748']
          }
          style={styles.orbGradient}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        />
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    width: 200,
    height: 200,
    alignItems: 'center',
    justifyContent: 'center',
  },
  glowRing: {
    position: 'absolute',
    borderRadius: 100,
    borderWidth: 2,
  },
  outerRing: {
    width: 180,
    height: 180,
    borderColor: 'rgba(102, 126, 234, 0.3)',
  },
  middleRing: {
    width: 160,
    height: 160,
    borderColor: 'rgba(102, 126, 234, 0.4)',
  },
  orb: {
    width: 120,
    height: 120,
    borderRadius: 60,
    overflow: 'hidden',
    shadowColor: '#667eea',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.5,
    shadowRadius: 20,
    elevation: 10,
  },
  orbGradient: {
    flex: 1,
  },
});
```

### 5.5 Home Screen

```typescript
// src/screens/HomeScreen.tsx

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';

import { useUserStore } from '../stores/userStore';

interface HomeScreenProps {
  navigation: any;
}

export function HomeScreen({ navigation }: HomeScreenProps) {
  const { user, companionName } = useUserStore();

  const startConversation = () => {
    navigation.navigate('Conversation');
  };

  return (
    <LinearGradient colors={['#1a1a2e', '#16213e']} style={styles.container}>
      <SafeAreaView style={styles.safeArea}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.greeting}>Hey {user?.name || 'there'} 👋</Text>
          <TouchableOpacity onPress={() => navigation.navigate('Settings')}>
            <Text style={styles.settingsIcon}>⚙️</Text>
          </TouchableOpacity>
        </View>

        {/* Main CTA */}
        <View style={styles.mainContent}>
          <Text style={styles.companionName}>{companionName || 'Koi'}</Text>
          <Text style={styles.subtitle}>is ready to talk</Text>

          <TouchableOpacity
            style={styles.callButton}
            onPress={startConversation}
            activeOpacity={0.8}
          >
            <LinearGradient
              colors={['#667eea', '#764ba2']}
              style={styles.callButtonGradient}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              <Text style={styles.callButtonIcon}>📞</Text>
              <Text style={styles.callButtonText}>Start Talking</Text>
            </LinearGradient>
          </TouchableOpacity>

          <Text style={styles.hint}>
            Tap to start a voice conversation
          </Text>
        </View>

        {/* Recent conversations */}
        <View style={styles.recentSection}>
          <Text style={styles.recentTitle}>Recent</Text>
          <TouchableOpacity style={styles.recentItem}>
            <Text style={styles.recentItemText}>Yesterday, 11:30 PM</Text>
            <Text style={styles.recentItemDuration}>23 min</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.recentItem}>
            <Text style={styles.recentItemText}>Feb 5, 9:15 PM</Text>
            <Text style={styles.recentItemDuration}>15 min</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
    paddingHorizontal: 20,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 20,
  },
  greeting: {
    color: '#fff',
    fontSize: 24,
    fontWeight: '600',
  },
  settingsIcon: {
    fontSize: 24,
  },
  mainContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  companionName: {
    color: '#fff',
    fontSize: 48,
    fontWeight: '700',
  },
  subtitle: {
    color: '#888',
    fontSize: 18,
    marginTop: 8,
    marginBottom: 40,
  },
  callButton: {
    borderRadius: 40,
    overflow: 'hidden',
    shadowColor: '#667eea',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 8,
  },
  callButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 20,
    paddingHorizontal: 40,
    gap: 12,
  },
  callButtonIcon: {
    fontSize: 24,
  },
  callButtonText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '600',
  },
  hint: {
    color: '#666',
    fontSize: 14,
    marginTop: 20,
  },
  recentSection: {
    marginBottom: 40,
  },
  recentTitle: {
    color: '#888',
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 12,
  },
  recentItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.1)',
  },
  recentItemText: {
    color: '#fff',
    fontSize: 16,
  },
  recentItemDuration: {
    color: '#888',
    fontSize: 14,
  },
});
```

---

## 6. Infrastructure Setup

### 6.1 LiveKit Cloud Setup

```bash
# Option 1: LiveKit Cloud (Recommended for MVP)
# 1. Sign up at https://cloud.livekit.io
# 2. Create a new project
# 3. Get your API Key and Secret
# 4. Note your WebSocket URL (wss://your-project.livekit.cloud)

# Option 2: Self-hosted LiveKit (For production scale)
# Deploy on AWS ECS or Kubernetes
```

### 6.2 Docker Compose (Development)

```yaml
# docker-compose.yml

version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: koi
      POSTGRES_PASSWORD: koi_dev_password
      POSTGRES_DB: koi
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis Cache
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Backend API
  api:
    build:
      context: ./api
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://koi:koi_dev_password@postgres:5432/koi
      - REDIS_URL=redis://redis:6379
      - LIVEKIT_API_KEY=${LIVEKIT_API_KEY}
      - LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}
      - LIVEKIT_URL=${LIVEKIT_URL}
      - SARVAM_API_KEY=${SARVAM_API_KEY}
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - postgres
      - redis

  # Voice Agent
  agent:
    build:
      context: ./agent
      dockerfile: Dockerfile
    environment:
      - LIVEKIT_API_KEY=${LIVEKIT_API_KEY}
      - LIVEKIT_API_SECRET=${LIVEKIT_API_SECRET}
      - LIVEKIT_URL=${LIVEKIT_URL}
      - SARVAM_API_KEY=${SARVAM_API_KEY}
      - DATABASE_URL=postgresql://koi:koi_dev_password@postgres:5432/koi
      - PINECONE_API_KEY=${PINECONE_API_KEY}
      - PINECONE_INDEX=koi-memories
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
```

### 6.3 Environment Variables

```bash
# .env

# LiveKit
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=wss://your-project.livekit.cloud

# Sarvam AI
SARVAM_API_KEY=your_sarvam_api_key

# Database
DATABASE_URL=postgresql://koi:password@localhost:5432/koi

# Redis
REDIS_URL=redis://localhost:6379

# Vector DB
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX=koi-memories

# Auth
JWT_SECRET=your_jwt_secret_min_32_chars

# Razorpay
RAZORPAY_KEY_ID=your_razorpay_key
RAZORPAY_KEY_SECRET=your_razorpay_secret
```

---

## 7. Cost Estimation (LiveKit + Sarvam)

### Monthly Costs at 1,000 DAU

| Service | Usage | Cost |
|---------|-------|------|
| **LiveKit Cloud** | 30,000 participant-minutes | ~$150 |
| **Sarvam STT** | 15,000 minutes | ~₹7,500 |
| **Sarvam TTS** | 10M characters | ~₹3,000 |
| **Sarvam LLM** | 20M tokens | ~₹2,000 |
| **Pinecone** | Starter tier | $0-70 |
| **AWS (Backend)** | ECS, RDS, Redis | ~₹15,000 |
| **Total** | | **~₹40,000/month** |

### At 10,000 DAU

| Service | Cost |
|---------|------|
| LiveKit | ~$1,000 |
| Sarvam APIs | ~₹50,000 |
| Pinecone | ~$70 |
| AWS | ~₹50,000 |
| **Total** | **~₹2,00,000/month** |

---

## 8. Development Timeline

### Week 1-2: Foundation
```
□ LiveKit account setup
□ React Native project setup
□ LiveKit + React Native integration
□ Basic voice connection working
□ Python agent skeleton
```

### Week 3-4: Sarvam Integration
```
□ Sarvam STT streaming
□ Sarvam LLM streaming
□ Sarvam TTS streaming
□ Full voice pipeline working
□ Basic conversation quality
```

### Week 5-6: App Polish
```
□ Onboarding flow
□ Home screen
□ Settings screen
□ Visual polish (animations)
□ Memory system basic
```

### Week 7-8: Production Ready
```
□ Auth system
□ Payment integration
□ Analytics
□ Error handling
□ TestFlight/Play Store beta
```

---

*This architecture document provides the foundation for a production-grade voice companion app.*
