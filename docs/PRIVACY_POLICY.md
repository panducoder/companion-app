# Koi Privacy Policy

**Last Updated:** February 2025
**Effective Date:** February 2025

---

## The Short Version

We built Koi to be your companion, not to exploit your data. Here is exactly what we collect, why, and what you can do about it.

- We process your voice in real-time. **We do NOT store voice recordings.**
- We store conversation text so Koi can remember you. **You can delete it anytime.**
- We never sell your data. Period.

---

## What Data We Collect

### 1. Account Information
- **Phone number:** Used for login (OTP verification). We store a hashed version.
- **Name:** What you tell us to call you. Stored in your profile.
- **Companion name:** What you choose to call Koi. Stored in your profile.

### 2. Voice Data
- **Voice audio:** Your voice is streamed in real-time to our AI service for transcription. **Voice recordings are NOT stored.** Audio is processed, converted to text, and discarded immediately.
- **Transcribed text:** The text version of what you say IS stored as part of your conversation history. This is what lets Koi remember your conversations.

### 3. Conversation Data
- **Messages:** Both your messages and Koi's responses are stored as text.
- **Conversation metadata:** When you talked, how long the conversation lasted, and a brief summary.
- **Memory summaries:** Short summaries of past conversations, stored in a vector database so Koi can recall relevant context.

### 4. Usage Data
- **Session information:** When you open the app, how long you talk, connection quality.
- **Device information:** Device type, OS version, app version. Used only for debugging.
- **Crash reports:** If the app crashes, we collect technical logs (no conversation content).

### 5. What We Do NOT Collect
- We do NOT store voice recordings.
- We do NOT collect your contacts, photos, or location.
- We do NOT read your other apps or messages.
- We do NOT use your data for advertising.

---

## Why We Collect This Data

| Data | Why We Need It |
|------|----------------|
| Phone number | To verify your identity and secure your account |
| Name | So Koi can address you personally |
| Conversation text | So Koi can remember past conversations and be a better companion |
| Memory summaries | So Koi can recall relevant things you have talked about before |
| Usage data | To fix bugs and improve the experience |

---

## How We Process Your Voice

When you speak to Koi, here is exactly what happens:

1. Your voice audio streams to our server over an encrypted connection (WebRTC).
2. The audio is sent to **Sarvam AI** for speech-to-text conversion.
3. Sarvam AI processes the audio and returns text. The audio is discarded.
4. The text is used to generate Koi's response.
5. Koi's response text is sent to Sarvam AI for text-to-speech conversion.
6. The generated audio streams back to your phone.

**At no point is your voice audio stored on any server.** Only the transcribed text is saved.

---

## Third-Party Services

We use the following third-party services to power Koi:

| Service | What It Does | What Data It Receives |
|---------|-------------|----------------------|
| **Sarvam AI** | Converts speech to text, generates responses, converts text to speech | Your voice audio (real-time, not stored), conversation text |
| **LiveKit** | Real-time voice streaming infrastructure | Audio stream (encrypted, not stored) |
| **Supabase** | User accounts and conversation storage | Account info, conversation text |
| **Pinecone** | Memory search (finding relevant past conversations) | Conversation summaries (anonymized embeddings) |

Each of these services has their own privacy policy. We have selected them for their commitment to data security.

---

## Your Rights

You have full control over your data:

### View Your Data
You can see all data we have about you in the app under **Settings > Privacy > Your Data**.

### Export Your Data
Tap **Settings > Privacy > Download My Data** to get a complete export of everything we have stored about you, including all conversation history and memories.

### Delete Your Data
Tap **Settings > Privacy > Delete All My Data** to permanently delete:
- Your profile information
- All conversation history
- All memory summaries
- Your account

This action is irreversible. Once deleted, Koi will not remember anything about you.

### Stop Using the Service
You can stop using Koi at any time by simply closing the app. Your data will remain until you delete it or until we receive a deletion request.

---

## Data Storage and Security

- **Where:** Your data is stored on servers located in **India** (Mumbai region).
- **Encryption:** All data is encrypted in transit (TLS 1.3) and at rest (AES-256).
- **Access:** Only essential engineering staff can access production data, and only for debugging with proper authorization.
- **Retention:** Conversation data is kept as long as your account is active. If you delete your account, all data is permanently removed within 30 days.

---

## Data We Never Share

We will NEVER:
- Sell your personal data or conversation content to anyone.
- Share your conversations with advertisers.
- Use your conversations to train AI models without your explicit opt-in consent.
- Share your data with other users.

We MAY share data only in these limited cases:
- **Legal requirement:** If required by law or valid legal process.
- **Safety:** If we believe someone is in immediate danger (e.g., credible threat of self-harm).
- **Aggregated analytics:** Non-personal, aggregated statistics (e.g., "average conversation length is 8 minutes"). This data cannot identify any individual.

---

## Children's Privacy

Koi is intended for users aged 13 and above. We do not knowingly collect personal information from children under 13. If you believe a child under 13 is using Koi, please contact us and we will delete their account.

---

## Changes to This Policy

We may update this privacy policy from time to time. If we make significant changes, we will notify you through the app before the changes take effect.

---

## Contact Us

If you have questions about your privacy or this policy:

- **Email:** privacy@koi.app
- **In-app:** Settings > About > Report a Problem

We aim to respond to all privacy inquiries within 48 hours.

---

*This privacy policy is written in plain language because we believe you deserve to actually understand what happens with your data.*
