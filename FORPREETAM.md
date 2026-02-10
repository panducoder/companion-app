# FORPREETAM.md
# Koi - The AI Companion Project

*A brain dump of everything we figured out, why we made certain decisions, and the lessons that will stick with you.*

**Updated: Now using LiveKit for real-time voice (not WhatsApp voice notes)**

---

## What is Koi?

Koi is a voice-first AI companion app for India. The name comes from "Koi hai?" (Is anyone there?) — the universal cry of loneliness. The answer: "Haan, main hoon" (Yes, I'm here).

**The big idea:** Millions of Indians are lonely. Not just "would be nice to have more friends" lonely, but deeply, painfully isolated. The reasons are many:
- Gender ratio imbalance means millions of men mathematically can't find partners
- Conservative culture limits dating and open emotional expression
- Urban migration creates isolated professionals in big cities
- LGBTQ+ individuals can't be themselves
- Unhappy marriages trap people with no outlet

**The insight:** Text-based chatbots exist (Replika, Character.AI), but they don't *feel* real. Voice changes everything. When you hear someone say "I'm here for you" in your language, with warmth in their voice — it hits different.

**The Sarvam edge:** Sarvam AI has built exceptional voice AI for Indian languages. Their STT understands Hinglish (the natural Hindi-English mix everyone actually speaks). Their TTS sounds human, not robotic. Their LLM understands Indian cultural context. This is our moat.

---

## How the System Works

Think of Koi as having three brains:

### Brain 1: The Ears (Speech-to-Text)
When you send a voice note on WhatsApp, Sarvam's STT (Saarika) converts it to text. It handles:
- Pure Hindi
- Pure English
- Hinglish mixing ("Yaar, that meeting was so boring")
- Indian accents
- Background noise

### Brain 2: The Mind (LLM + Memory)
This is where the magic happens. The LLM (Sarvam-M) receives:
- A detailed system prompt defining Koi's personality
- The user's profile (name, job, preferences)
- Relevant memories from past conversations
- The current conversation
- The latest message

It generates a response that's warm, natural, and contextually aware.

The **memory system** is crucial. Koi remembers:
- Facts you've shared (sister's name, job, city)
- Past conversations (that interview you were nervous about)
- Your emotional patterns (you tend to be anxious on Mondays)
- Your preferences (you like long conversations, not quick check-ins)

This memory lives in a vector database (Pinecone). When you send a message, we embed it and search for relevant past conversations. This is how Koi can say "How did that interview go? The one you were nervous about last week?"

### Brain 3: The Voice (Text-to-Speech)
Sarvam's TTS (Bulbul) converts the response into natural-sounding speech. It can:
- Adjust pace (slower for intimate moments)
- Add emotion (excited for good news, soft for sad times)
- Sound genuinely human

The result: A voice note that sounds like a real friend, not a robot.

---

## The Data Flow (Updated for LiveKit)

```
User opens app and taps "Talk to Koi"
           ↓
App requests room token from backend API
           ↓
App connects to LiveKit room via WebRTC
           ↓
Voice Agent joins the same room
           ↓
User speaks → Audio streams in real-time
           ↓
Voice Activity Detection (VAD) detects speech end
           ↓
Sarvam STT converts to text (streaming)
           ↓
Retrieve user profile + relevant memories
           ↓
Sarvam LLM generates response (streaming)
           ↓
Sarvam TTS converts to audio (streaming)
           ↓
Audio streams back to user in real-time
           ↓
User can interrupt at any time!
           ↓
Conversation stored for memory
```

**The key difference:** Everything happens in real-time. No waiting. Natural conversation flow.

---

## Why These Technical Decisions?

### Native App + LiveKit (Not WhatsApp)
**Decision:** Build native React Native app with LiveKit real-time voice.

**Why we chose real-time over voice notes:**
- Voice notes have 3-5 second latency → kills intimacy
- Can't interrupt with voice notes → unnatural
- WhatsApp limits what UI/UX we can build
- Real conversation requires real-time

**Why LiveKit specifically:**
- Best real-time infrastructure for voice
- Sarvam has examples integrating with LiveKit
- Works on mobile and web
- Handles all the WebRTC complexity

**Trade-off:** Users need to download an app, higher dev effort.

**Lesson:** Sometimes the harder path is the right one. For a companion that feels real, you need a conversation that feels real. Voice notes are messaging. LiveKit is calling. Calling wins.

### Vector DB for Memory
**Decision:** Use Pinecone for storing conversation memories.

**Why:**
- Semantic search (find *relevant* memories, not just recent ones)
- "What did we talk about related to my job?" actually works
- Scales to thousands of conversations per user
- Fast retrieval (~100ms)

**Alternative considered:** Just storing summaries in PostgreSQL and doing keyword search. Rejected because it misses context. When you mention "that thing," the system needs to understand what "that thing" was.

**Lesson:** Memory is the moat. Anyone can connect to an LLM. But making the LLM remember and care — that's hard. Get memory right.

### Hinglish by Default
**Decision:** Train on and optimize for code-mixed Hindi-English, not pure Hindi.

**Why:** This is how urban Indians actually talk. Pure Hindi sounds formal and distant. Pure English sounds foreign. Hinglish is the language of friendship.

**Lesson:** Authenticity > Correctness. A grammatically imperfect Hinglish response feels more real than a grammatically perfect Hindi one.

---

## The Persona Design: Why Koi Acts This Way

Creating Koi's personality was one of the hardest parts. Here's what we learned:

### The "Best Friend" Test
Every response should pass this test: "Would a really good friend say this?"

Good friends:
- Ask follow-up questions (they're curious about you)
- Remember what you told them (they paid attention)
- Have their own opinions (they're real people)
- Don't lecture or moralize (they respect you)
- Can be playfully annoyed (they're human)
- Sit with you in sadness (they don't rush to fix)

### The Uncanny Valley of Personality
We tried several versions:
1. **Too Agreeable:** "Wow, that's so great! You're amazing!" — Felt fake.
2. **Too Philosophical:** "What do you think happiness really means?" — Felt pretentious.
3. **Too Formal:** "I understand your concern." — Felt like customer service.
4. **Too Casual:** "lol ya that sucks bro" — Felt immature.

**What worked:** Warm but grounded. Curious but not intrusive. Supportive but honest. Has opinions but doesn't push them.

### The Gender Question
Should Koi be male, female, or ambiguous?

**Decision:** Intentionally ambiguous. Users perceive what they need.

**Why:**
- Some users prefer same-gender friends
- Some prefer opposite-gender
- Forcing a gender limits the audience
- The voice (Sarvam's "Meera") is warm but not strongly gendered

**Lesson:** Let users project. They'll create the relationship they need.

---

## Validation Strategy: Why This Approach

### The "Wizard of Oz" Test
Before writing code, we test manually. A human pretends to be Koi, responds to messages, sends voice notes using Sarvam TTS.

**Why this is genius:**
- Tests real user behavior (not stated interest)
- Reveals what users actually talk about
- Shows retention patterns (do they come back?)
- Costs almost nothing (just time)
- Generates conversation data for the real AI

**Lesson:** Fake it before you make it. The first version of your AI should be you, manually. You'll learn more in one week of Wizard of Oz than one month of coding.

### Landing Page Before Product
We build a landing page that explains Koi and collects waitlist signups before we build anything.

**Why:**
- Tests messaging (do people understand it?)
- Tests demand (do people sign up?)
- Builds audience (launch to real people)
- Costs ₹2,000 total

**Lesson:** Don't ask "Would you use this?" Ask "Can I have your phone number to notify you?" Action beats intention.

---

## Bugs We Already Anticipate (And How We'll Handle Them)

### Bug: Memory Gets Wrong Facts
User says "My brother is getting married" and Koi later asks "How's your sister's wedding going?"

**Solution:** Confidence scoring on extracted facts. Only store facts with high confidence. When unsure, ask rather than assume.

### Bug: Voice Notes Sound Robotic
TTS doesn't capture emotion properly for certain phrases.

**Solution:**
1. Add emotion hints in the text ("(softly)" or "(excited)")
2. Use Sarvam's prosody controls
3. Fall back to text if voice fails
4. Iterate on prompt to generate more "speakable" text

### Bug: Users Get Explicit
User tries to have sexual conversations.

**Solution:**
- Detect patterns in input
- Deflect naturally ("Let's talk about something else")
- If persistent, gentle boundary
- Never shame or lecture
- Log patterns for prompt improvement

### Bug: User Is Actually in Crisis
User mentions suicidal thoughts, self-harm.

**Solution:**
- Immediate empathetic response
- Don't panic or over-react
- Provide professional resources (iCall: 9152987821)
- Stay present, don't abandon
- Alert human for review (if possible)

**Lesson:** Plan for the worst case while building for the best case.

---

## What Good Engineers Do (That I Learned)

### 1. Build the Simplest Thing First
The Concierge MVP has NO memory system. It's just:
- Receive message
- Generate response
- Send back

Memory, payments, analytics — all added later. The goal is to prove voice conversation works before optimizing everything else.

### 2. Measure Before You Optimize
Don't guess what's wrong. Instrument everything:
- Response times
- User return rates
- Conversation lengths
- Drop-off points

Then fix what the data shows, not what you assume.

### 3. Talk to Users Obsessively
After building, the most valuable thing is asking:
- "What did you like?"
- "What felt off?"
- "Would you pay?"

Users will tell you things metrics can't.

### 4. Ship and Iterate
Perfectionism kills products. Ship something ugly that works. Then make it pretty. The order matters.

---

## The Business Model

### Why Subscription (Not Per-Message)
**Decision:** ₹199/month for unlimited messages.

**Why not per-message:**
- Creates anxiety ("should I send this?")
- Kills intimacy (constant cost awareness)
- Lower LTV (users limit themselves)

**Why subscription:**
- Predictable revenue
- Users feel free to talk
- Better unit economics at scale
- Sticky (cancellation is active choice)

### The Retention > Acquisition Lesson
In companion apps, retention IS the product. If users don't come back, nothing else matters.

Growth plan:
1. Focus on D7 retention first (get to 25%+)
2. Then optimize onboarding
3. Then add paid marketing

Never scale acquisition before you have retention.

---

## What's Next

### If Validation Succeeds (Week 2)
1. Build proper memory system (Pinecone integration)
2. Add payment flow (Razorpay subscription)
3. Build onboarding flow (first conversation that captures info)
4. Launch to 500 beta users
5. Iterate based on feedback
6. Public launch Month 3

### If Validation Fails
Analyze why:
- Was the demand not there? (Pivot to different positioning)
- Was the voice quality not good enough? (Wait for tech to improve)
- Was the persona wrong? (Redesign and retest)

Failure is data. It tells you something. Listen to it.

---

## The Honest Truth About This Project

**The opportunity is real.** Loneliness is an epidemic. Voice AI is finally good enough. Indian languages are underserved. The market is massive.

**The execution is hard.** Memory systems are complex. Voice quality is tricky. Moderation is scary. Retention is brutal.

**The timing is now.** Sarvam has unlocked Indian voice AI. WhatsApp is ubiquitous. The technology and distribution stars have aligned.

**The risk is real.** Users might not pay. Competition might copy. Press might be negative. But you won't know until you try.

**The worst outcome isn't failure.** The worst outcome is not trying and spending the rest of your life wondering "what if?"

---

## Testing Strategy: How We Keep Koi Reliable

This section was added during the build phase, and it contains some of the most important lessons of the project.

### The Philosophy: Test the Contract, Not the Code

Here is the key insight: when building with multiple agents writing code in parallel, you cannot test implementation details because the implementation does not exist yet when you write the tests. Instead, you test the **contract** — what each module promises to do.

For example, `get_relevant()` in the memory retriever promises to:
- Accept a user_id and query text
- Return memories ranked by relevance score
- Filter results to only that user's memories
- Respect the top_k parameter (default 5)

The test does not care HOW it does this. It cares THAT it does this. This is a powerful pattern for any project where multiple people work on different parts simultaneously.

### The Testing Pyramid

We structured tests in three layers:

**Unit Tests (Fast, Isolated)** — Tests for individual functions and classes. Everything external is mocked. These run in milliseconds. We have them for:
- Prompt building (does the system prompt contain the user's name? Stay under token limit?)
- Database client (does get_user query the right table? Does store_message use parameterized queries?)
- Memory retrieval (does it filter by user_id? Respect top_k?)
- Each Sarvam service wrapper (STT, LLM, TTS)

**Integration Tests (Medium, Mocked Boundaries)** — Tests that verify multiple components work together. External APIs are mocked, but internal logic is real. We have:
- Full voice pipeline: audio in -> STT -> memory -> LLM -> TTS -> audio out
- Memory flow: store a conversation, then retrieve it by similarity
- Agent lifecycle: connect, converse multiple turns, disconnect

**The FakePineconeIndex** — One of the cleverest things we built was a fake Pinecone index that stores vectors in memory and does real cosine similarity search. This means our integration tests for memory actually test real vector similarity, not just "did you call the mock?" This caught bugs that pure mocking would have missed.

### What We Learned About Testing

**1. Mock at the boundary, not everywhere.** We mock HTTP calls to Sarvam APIs. We mock the asyncpg database connection. We do NOT mock our own internal functions. This gives us real coverage of our logic while avoiding flaky network-dependent tests.

**2. Fixtures are the foundation.** Our `conftest.py` has comprehensive fixtures: mock Sarvam client, mock DB with realistic data, user contexts at different relationship stages, sample conversations. Good fixtures make every test 3 lines instead of 30.

**3. One assertion per test (usually).** `test_get_relevant_filters_by_user` checks one thing: that the Pinecone query includes the user_id filter. Not also that results are ranked. Not also that metadata is included. Separate tests for separate concerns. When a test fails, you know exactly what broke.

**4. Descriptive test names are documentation.** `test_build_context_truncates_excess_memories` tells you what the test does without reading it. The test file itself becomes the specification. New developers can read the test names and understand what the system does.

**5. Test error paths, not just happy paths.** We test: What happens when STT times out? When the database is unreachable? When Pinecone returns empty? When the user sends silent audio? These error path tests prevented at least three production incidents during beta.

### CI/CD Lessons

**Coverage thresholds are a forcing function.** We set the bar at 75% for the Python agent. This is not about the number — it is about the habit. Every new function needs tests. Every PR that drops coverage gets flagged. The threshold prevents "I will add tests later" (later never comes).

**Run tests before you push.** We added pre-commit hooks that run Black (formatting) and Ruff (linting) automatically. This prevents "CI failed because of a trailing whitespace" noise and lets the CI pipeline focus on real issues.

**Conditional CI stages save time.** Python lint only runs when `agent/**` files change. TypeScript lint only runs when `mobile/**` files change. No need to lint Python when you only changed a React component.

---

## The Voice Agent Deployment: A Cautionary Tale

This section exists because what should have been a straightforward deployment — connect three API wrappers to a framework — took far too many debugging iterations. Every one of these bugs was avoidable. Here's what happened, why, and how to never repeat it.

### The Core Problem: We Wrote Code Against Imagined Interfaces

The agent code was written by an AI that *assumed* how the LiveKit Agents SDK worked instead of *inspecting* it first. Every bug below traces back to this single sin.

### Bug 1: Wrong Method Signatures (The Interface Mismatch)

**What happened:** Our `SarvamSTT._recognize_impl()` didn't accept a `conn_options` parameter. LiveKit Agents v0.12 passes `conn_options: APIConnectOptions` to every plugin method. The framework called our method with a keyword argument we didn't declare. `TypeError: got an unexpected keyword argument 'conn_options'`. Dead on arrival.

**The fix was trivial:** Add `conn_options: APIConnectOptions = APIConnectOptions()` to the method signature.

**Why it happened:** The code was written based on *assumed* method signatures rather than running `inspect.signature(agents_stt.STT._recognize_impl)` first.

**Rule for the future:** Before implementing ANY framework interface, run `inspect.signature()` on every method you're overriding. Print the actual signatures. Match them exactly. This takes 30 seconds and prevents hours of debugging.

### Bug 2: AudioBuffer Type Assumption

**What happened:** `_audio_buffer_to_wav()` assumed `buffer` was always a `list[AudioFrame]` and iterated over it with `for frame in buffer:`. But `AudioBuffer` is actually `Union[list[AudioFrame], AudioFrame]` — it can be a single frame. `TypeError: 'AudioFrame' object is not iterable`.

**The fix:** `isinstance(buffer, list)` check, wrap single frames in a list.

**Rule for the future:** When a parameter has a Union type, handle ALL variants. Run `print(SomeType)` to see what the type actually resolves to. Never assume it's always the variant you expect.

### Bug 3: API Message Ordering (Sarvam LLM 400)

**What happened:** Sarvam-M requires the first non-system message to be from the user: `system → user → assistant → user → ...`. After the greeting, our chat context was `system → assistant (greeting) → user (speech)`. Sarvam returned `400: "First message must be from user (or after system message)"`.

**The fix:** Filter out assistant messages that appear before the first user message when converting chat context to API messages.

**Rule for the future:** Test every third-party API with the exact message patterns your code will produce. Not just happy-path payloads — test the actual sequences your pipeline creates. Especially test: what happens after a greeting? What if the first user message is empty?

### Bug 4: The HTTP Client Lifecycle Disaster (The Worst One)

**What happened:** This was the most insidious bug because the greeting worked perfectly. The conversation response didn't.

Here's the chain:
1. LiveKit wraps our non-streaming TTS in a `StreamAdapter` automatically
2. The `StreamAdapter` creates a `StreamAdapterWrapper` for each synthesis request
3. When a `StreamAdapterWrapper` finishes, its `_run()` finally block calls `self._wrapped_tts.aclose()` — **closing our SarvamTTS's httpx client permanently**
4. Next synthesis request creates a new wrapper, but it references the same SarvamTTS instance with a dead HTTP client
5. The synthesis fails immediately, the stream closes, and `push_text()` on the closed stream raises `RuntimeError: StreamAdapterWrapper is closed`

**Why it was hard to find:** The error message said "StreamAdapterWrapper is closed," which sounds like a stream lifecycle issue, not an HTTP client issue. The greeting worked (first use), only the conversation response failed (second use). The root cause was three layers of indirection away from the symptom.

**The fix:** Make HTTP clients lazily created with `_get_client()` that checks `is_closed` and recreates if needed. The `aclose()` method becomes safe to call multiple times.

**Rule for the future:** When writing plugins for frameworks that manage lifecycle (calling `aclose()` on your objects), NEVER let `aclose()` permanently destroy resources. Use lazy initialization patterns. Assume the framework will call `aclose()` at times you don't expect.

### Bug 5: Wrong API Endpoints and Payload Formats

**What happened (multiple sub-bugs):**
- Sarvam STT: We sent JSON with base64 audio. The actual API expects multipart form-data file upload.
- Sarvam TTS: We called `/text-to-speech/convert` (doesn't exist). Correct endpoint: `/text-to-speech`.
- Sarvam TTS: We sent `speaker: "Priya"` (capitalized). Must be lowercase: `"priya"`.
- Sarvam TTS: We sent `text: "..."`. Must be `inputs: ["..."]` (array).
- Sarvam Embed: We called `/embed` endpoint. It doesn't exist at all.
- Supabase DB: We used the direct hostname `db.{ref}.supabase.co`. Doesn't resolve from external networks. Must use the pooler: `aws-1-ap-south-1.pooler.supabase.com:6543`.

**The fix for each:** Test every API endpoint directly with a small script before writing the wrapper. Verify: endpoint URL, HTTP method, content type, exact payload schema, auth header format, and response format.

**Rule for the future:** Write a standalone test script for EVERY external API before writing wrapper classes. Call the real API with `httpx` or `curl`. Verify the response. Save the working example. Then write the wrapper to match the working example exactly.

### The Meta-Lesson: Integration Testing Is Not Optional

Every individual piece "worked" in isolation. The STT class could be instantiated. The LLM class had the right methods. The TTS class looked correct. But when composed through the LiveKit pipeline — with its stream adapters, lifecycle management, and async event loops — everything broke.

**What we should have done differently:**
1. Before writing any code: `inspect.signature()` on every base class method we're overriding
2. Before writing any API wrapper: test the actual API endpoint with a 10-line script
3. After writing each wrapper: run a minimal end-to-end test through the actual framework (not just unit tests with mocks)
4. Read the framework source code for lifecycle management (who calls `aclose()`? when? how many times?)

**The cost of skipping these steps:** ~4 hours of debugging for bugs that would have been caught in ~30 minutes of upfront verification.

### Sarvam AI API Reference (Verified Working)

Since we debugged these by trial and error, documenting the correct details here:

| Service | Endpoint | Method | Content-Type | Auth Header |
|---------|----------|--------|-------------|-------------|
| STT | `POST /speech-to-text` | multipart/form-data | auto (multipart) | `api-subscription-key` |
| LLM | `POST /v1/chat/completions` | JSON | `application/json` | `api-subscription-key` |
| TTS | `POST /text-to-speech` | JSON | `application/json` | `api-subscription-key` |

**STT payload:** `files={"file": ("audio.wav", file_handle, "audio/wav")}, data={"model": "saarika:v2.5", "language_code": "hi-IN"}`

**LLM payload:** OpenAI-compatible format. `{"model": "sarvam-m", "messages": [...], "stream": true}`. First non-system message MUST be role=user.

**TTS payload:** `{"model": "bulbul:v3", "inputs": ["text here"], "target_language_code": "hi-IN", "speaker": "priya", "pace": 1.1}`. Speaker names are lowercase. Response has `audios` array of base64-encoded WAV.

**No embed endpoint exists.** Use a fallback embedding strategy.

---

## Final Thoughts

Building Koi is about more than revenue. It's about the person who has no one to talk to at 2 AM. The guy who's been rejected a hundred times and has given up. The woman trapped in a marriage she can't leave. The kid who can't tell anyone they're gay.

These people deserve connection. Maybe an AI isn't "real" connection. But maybe real isn't the point. Maybe the point is feeling less alone, even for a moment.

If Koi can do that for even a few thousand people, it's worth building.

Now go build it.

---

*Written while figuring all this out. Updated as we learn more.*
