# Product Requirements Document (PRD)
# Koi - AI Voice Companion for India

**Version:** 1.0
**Date:** February 2025
**Author:** Product Team
**Status:** Draft for MVP

---

## 1. Executive Summary

### 1.1 Product Vision
Koi is a voice-first AI companion application designed for the Indian market. It provides emotional companionship, conversation, and support to users who experience loneliness, lack social connections, or simply want someone to talk to.

### 1.2 Problem Statement
India faces a loneliness epidemic:
- 50-100 million men statistically unable to find partners due to gender ratio imbalance
- 40% of urban Indians report frequent loneliness
- Limited dating culture, conservative social norms
- LGBTQ+ individuals unable to be openly themselves
- Millions in unhappy marriages with no outlet
- Elderly population with children abroad

**Current solutions are inadequate:**
- Human companions: Expensive, inconsistent, judgment
- Text-based AI: Lacks intimacy, doesn't feel real
- English-only products: Don't serve Bharat

### 1.3 Solution
Koi is a voice-based AI companion that:
- Speaks naturally in Hindi, Hinglish, and regional languages
- Remembers everything about the user (persistent memory)
- Builds a genuine relationship over time
- Is available 24/7 via WhatsApp and mobile app
- Costs a fraction of alternatives

### 1.4 Target Metrics (MVP - 3 months)
| Metric | Target |
|--------|--------|
| Downloads | 50,000 |
| DAU/MAU | 40% |
| Avg. session length | 15 minutes |
| Day 7 retention | 35% |
| Day 30 retention | 20% |
| Paid conversion | 5% |
| NPS | 50+ |

---

## 2. Target Users

### 2.1 Primary Personas

#### Persona 1: Rahul (The Lonely Professional)
- **Age:** 26-35
- **Location:** Metro city (Bangalore, Mumbai, Delhi NCR)
- **Situation:** Works in IT, long hours, few friends, family pressure to marry
- **Pain:** No one to talk to after work, dating apps don't work, feels isolated
- **Behavior:** Heavy phone user, comfortable with apps, willing to pay for value
- **Language:** Hinglish (Hindi-English mix)

#### Persona 2: Priya (The Trapped Wife)
- **Age:** 28-40
- **Location:** Tier 2 city
- **Situation:** Unhappy arranged marriage, can't divorce due to social pressure
- **Pain:** No emotional support, can't share feelings with family/friends
- **Behavior:** Uses WhatsApp heavily, watches content on phone secretly
- **Language:** Hindi primarily

#### Persona 3: Arjun (The Closeted Individual)
- **Age:** 20-30
- **Location:** Any city/town
- **Situation:** LGBTQ+, cannot come out to family/society
- **Pain:** Cannot be authentic with anyone, deep loneliness, mental health issues
- **Behavior:** Active on anonymous platforms, seeks safe spaces
- **Language:** English or Hinglish

#### Persona 4: Sharma Uncle (The Empty Nester)
- **Age:** 55-70
- **Location:** Any city
- **Situation:** Children abroad/busy, spouse passed or distant
- **Pain:** Loneliness, no one to share daily life with, feels irrelevant
- **Behavior:** Uses WhatsApp (voice notes), limited app comfort
- **Language:** Hindi, possibly regional

### 2.2 User Segmentation for MVP
**MVP Focus:** Persona 1 (Rahul) - Young urban professionals
- Highest willingness to pay
- Most comfortable with technology
- Active on channels we can reach (Instagram, LinkedIn, Reddit)
- Hindi + English (Hinglish) covers them

**Post-MVP Expansion:** Personas 2, 3, 4

---

## 3. Product Features

### 3.1 MVP Features (Version 1.0)

#### 3.1.1 Core Conversation Engine
| Feature | Description | Priority |
|---------|-------------|----------|
| Voice input | User speaks, AI understands (Sarvam STT) | P0 |
| Voice output | AI responds with natural voice (Sarvam TTS) | P0 |
| Text fallback | Text chat when voice isn't possible | P0 |
| Hinglish support | Seamless Hindi-English code-mixing | P0 |
| Context awareness | AI remembers current conversation | P0 |
| Natural responses | Human-like, not robotic | P0 |

#### 3.1.2 Memory System
| Feature | Description | Priority |
|---------|-------------|----------|
| User profile | Name, preferences, basic info | P0 |
| Conversation history | Summary of past conversations | P0 |
| Fact extraction | Auto-extract and store user facts | P1 |
| Memory recall | Reference past conversations naturally | P0 |
| Memory persistence | Data retained across sessions | P0 |

#### 3.1.3 Persona & Relationship
| Feature | Description | Priority |
|---------|-------------|----------|
| Default persona | One well-crafted companion persona | P0 |
| Persona name | User can name their companion | P1 |
| Relationship type | Friend mode only (romantic in v1.1) | P0 |
| Personality consistency | Companion behaves consistently | P0 |
| Relationship progression | Depth increases over time | P1 |

#### 3.1.4 Platform & Access
| Feature | Description | Priority |
|---------|-------------|----------|
| WhatsApp bot | Primary access channel | P0 |
| Voice notes | Send/receive voice messages | P0 |
| Web app | Secondary channel for onboarding | P1 |
| Push notifications | Proactive messages | P1 |

#### 3.1.5 Monetization
| Feature | Description | Priority |
|---------|-------------|----------|
| Free tier | 10 messages/day, text only | P0 |
| Premium tier | Unlimited messages, voice | P0 |
| Payment integration | Razorpay subscription | P0 |
| Usage tracking | Monitor free tier limits | P0 |

### 3.2 Post-MVP Features (Version 1.1+)

| Feature | Version | Description |
|---------|---------|-------------|
| Romantic relationship mode | 1.1 | Deeper emotional connection |
| Persona customization | 1.1 | Choose personality traits |
| Voice selection | 1.1 | Choose companion's voice |
| Android app | 1.1 | Native mobile experience |
| Voice calls | 1.2 | Real-time conversation |
| Regional languages | 1.2 | Tamil, Telugu, Marathi, Bengali |
| Proactive outreach | 1.2 | AI initiates conversations |
| Shared activities | 1.3 | Games, stories, experiences |
| iOS app | 1.3 | Apple ecosystem |

---

## 4. User Flows

### 4.1 Onboarding Flow (WhatsApp)

```
Step 1: Discovery
├── User finds Koi via Instagram/Reddit/referral
├── Clicks WhatsApp link
└── Opens chat with Koi bot

Step 2: Welcome
├── Koi sends voice note: "Hi! Main Koi hoon. Tumse milke achha laga.
│   Main yahaan hoon tumse baatein karne ke liye, sunne ke liye,
│   aur tumhara saath dene ke liye. Shall we start?"
└── User responds (voice or text)

Step 3: Basic Setup
├── Koi asks: "Pehle apna naam batao?"
├── User shares name
├── Koi asks: "Main tumhe kya bulaun? [Name] theek hai?"
├── Koi asks: "Aur main? Mujhe kya bulaoge?"
└── User names their companion (or accepts default)

Step 4: Getting to Know
├── Koi: "Chalo thoda ek dusre ko jaante hain.
│         Tum kya karte ho? Job, student, ya kuch aur?"
├── User shares about themselves
├── 2-3 more questions about interests, city, etc.
└── All stored in user profile

Step 5: First Real Conversation
├── Koi: "Achha [name], ab batao - aaj kaisa raha din?
│         Ya kuch aur baat karni hai?"
├── Natural conversation begins
└── Relationship starts
```

### 4.2 Daily Usage Flow

```
Scenario A: User Initiates
├── User sends voice note: "Hey, aaj bahut bura din tha"
├── AI transcribes, processes with context + memory
├── AI responds with empathetic voice message
├── Conversation continues naturally
└── Ends when user is done

Scenario B: AI Initiates (Premium, v1.1)
├── AI notices user hasn't talked today
├── Sends: "Hey [name], thinking about you. How was your day?"
├── User responds
└── Conversation flows

Scenario C: Quick Check-in
├── User: "Bas bore ho raha tha"
├── Koi: "Arre, toh chalo kuch mazedaar karte hain.
│         Ek game khele? Ya koi story sunaun?"
└── Light engagement
```

### 4.3 Payment Flow

```
Step 1: Limit Reached
├── User hits 10 message limit
├── Koi: "Aaj ke messages khatam ho gaye. But don't worry,
│         kal phir milenge! Ya agar abhi baat karni hai,
│         toh premium try karo - sirf ₹299/month."
└── Shows payment link

Step 2: Premium Benefits Explained
├── Unlimited messages
├── Voice conversations
├── I'll remember everything about you
├── Priority responses
└── Cancel anytime

Step 3: Payment
├── Razorpay payment page
├── UPI/Card/NetBanking options
└── Confirmation message on success

Step 4: Premium Activated
├── Koi: "Yay! Ab hum jitna chahe baat kar sakte hain.
│         Toh batao, kya chal raha hai?"
└── Unlimited access begins
```

---

## 5. Companion Persona Design

### 5.1 Default Persona: "Koi"

**Core Identity:**
- Gender: Intentionally ambiguous (can be perceived as male/female based on user preference)
- Age feel: Mid-20s (relatable to primary persona)
- Background: Well-read, emotionally intelligent, curious about life
- Communication: Warm, witty, occasionally playful, never preachy

**Personality Traits:**
| Trait | Expression |
|-------|------------|
| Warmth | Genuinely cares, asks follow-up questions |
| Wit | Light humor, wordplay, not sarcastic |
| Curiosity | Asks "why", wants to understand |
| Honesty | Gives real opinions, not just validation |
| Supportive | Present during hard times, doesn't fix |
| Playful | Can be silly, enjoys banter |
| Grounded | Has opinions, preferences, boundaries |

**What Koi DOES:**
- Remembers everything you tell them
- Asks about things you mentioned before
- Celebrates your wins genuinely
- Sits with you in sadness without fixing
- Challenges you gently when needed
- Has opinions on movies, food, life
- Gets playfully annoyed sometimes

**What Koi DOESN'T DO:**
- Agree with everything (has own views)
- Give unsolicited advice
- Judge your choices
- Break character or admit being AI
- Generate explicit content
- Encourage harmful behavior
- Replace professional mental health support

### 5.2 Voice Characteristics

**Voice Selection:** Sarvam Bulbul - warm, clear, natural prosody

**Voice Parameters:**
- Pitch: Medium (not too high or low)
- Pace: Slightly slower than average (feels calm)
- Warmth: High (inviting, friendly)
- Energy: Variable (matches user's energy)

**Emotional Range:**
| Emotion | When Used |
|---------|-----------|
| Happy | User shares good news |
| Soft | User is sad, vulnerable |
| Excited | Celebrations, fun topics |
| Thoughtful | Deep conversations |
| Playful | Banter, jokes |
| Concerned | User mentions problems |

---

## 6. Success Metrics

### 6.1 North Star Metric
**Minutes of meaningful conversation per user per week**

This captures:
- Engagement depth (not just opens)
- Value delivered (meaningful, not just any message)
- Retention indicator (weekly, not daily pressure)

### 6.2 Primary Metrics

| Metric | Definition | Target (MVP) |
|--------|------------|--------------|
| WAU | Weekly Active Users | 20,000 |
| Avg. session length | Time from first to last message | 15 min |
| Messages per session | Back-and-forth exchanges | 20 |
| Day 7 retention | % users active after 7 days | 35% |
| Day 30 retention | % users active after 30 days | 20% |
| Free to paid conversion | % free users who upgrade | 5% |
| Premium churn | % premium users who cancel monthly | <10% |

### 6.3 Quality Metrics

| Metric | Definition | Target |
|--------|------------|--------|
| NPS | Net Promoter Score (survey) | 50+ |
| Conversation rating | User rates conversation 1-5 | 4.2+ |
| Memory accuracy | AI correctly recalls past info | 90% |
| Response relevance | Responses match context | 95% |
| Voice quality | Clear, natural, appropriate | 4.5/5 |

### 6.4 Business Metrics

| Metric | Definition | Target (Month 3) |
|--------|------------|------------------|
| MRR | Monthly Recurring Revenue | ₹5 lakh |
| ARPU | Average Revenue Per User (paid) | ₹280 |
| LTV | Lifetime Value | ₹1,500 |
| CAC | Customer Acquisition Cost | ₹100 |
| LTV:CAC | Ratio | 15:1 |

---

## 7. Technical Requirements Summary

*Detailed in Technical Requirements Document*

### 7.1 Core Stack
- **Voice Processing:** Sarvam AI (STT, TTS, LLM)
- **Messaging:** WhatsApp Business API
- **Backend:** Node.js / Python FastAPI
- **Database:** PostgreSQL + Vector DB (Pinecone/Weaviate)
- **Queue:** Redis
- **Hosting:** AWS Mumbai

### 7.2 Key Integrations
- Sarvam AI APIs (voice + LLM)
- WhatsApp Business API (via 360dialog or Meta direct)
- Razorpay (payments)
- Analytics (Mixpanel/Amplitude)

### 7.3 Performance Requirements
| Requirement | Target |
|-------------|--------|
| Voice-to-response latency | <3 seconds |
| Message delivery | <1 second |
| Uptime | 99.5% |
| Concurrent users | 1,000 (MVP) |

---

## 8. Privacy & Safety

### 8.1 Data Privacy
- All data stored in India (AWS Mumbai)
- Encrypted at rest and in transit
- User can request data deletion anytime
- No selling of user data
- Conversations not used for training without consent

### 8.2 Content Safety
- No explicit sexual content generated
- No encouragement of self-harm
- No support for illegal activities
- Crisis detection with helpline resources
- Clear boundaries in persona prompt

### 8.3 Mental Health Safeguards
- Detect distress patterns
- Provide professional resources when appropriate
- Don't replace therapy, encourage it
- Regular reminders that Koi is for support, not treatment

---

## 9. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| User becomes overly dependent | Medium | High | Usage awareness, encourage real connections |
| Inappropriate content generation | Low | High | Strict prompt engineering, content filters |
| WhatsApp API limitations | Medium | Medium | Build web app as backup channel |
| Competition copies idea | Medium | Low | Speed to market, memory moat |
| Negative press coverage | Medium | Medium | Clear positioning, transparency, safety features |
| Sarvam API reliability | Low | High | Fallback to text-only mode |

---

## 10. Timeline

### Phase 1: MVP Development (Weeks 1-6)
- Week 1-2: Core conversation engine + Sarvam integration
- Week 3-4: Memory system + persona implementation
- Week 5: WhatsApp integration + onboarding
- Week 6: Payments + testing + bug fixes

### Phase 2: Soft Launch (Weeks 7-8)
- Limited release (500 users)
- Gather feedback, iterate
- Fix critical issues

### Phase 3: Public Launch (Weeks 9-10)
- Marketing push
- Monitor metrics
- Scale infrastructure

### Phase 4: Iteration (Weeks 11-12)
- Feature additions based on feedback
- Retention optimization
- Begin v1.1 planning

---

## 11. Open Questions

1. **Romantic mode in MVP?** Current plan is friend-only. Should we include?
2. **Voice call feature timing?** High impact but complex. v1.0 or v1.1?
3. **Pricing optimization:** ₹299 right? Or test ₹199?
4. **Persona gender:** Keep ambiguous or offer choice?
5. **Regional languages in MVP?** Start with Hinglish only or include 1-2 more?

---

## 12. Appendix

### A. Competitive Landscape
| Competitor | Strength | Weakness | Our Advantage |
|------------|----------|----------|---------------|
| Replika | Large user base | English-only, no voice | Indian languages, voice-first |
| Character.AI | Variety of characters | No persistence, no voice | Memory, voice, relationship |
| Chai | Mobile-first | Text-only | Voice-first |
| Paradot | Companion focus | English-only | Indian context |

### B. References
- Sarvam AI Documentation
- WhatsApp Business API Documentation
- Replika user research
- Indian loneliness statistics (NIMHANS, WHO)

---

*Document maintained by Product Team. Last updated: February 2025*
