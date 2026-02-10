# Validation Plan
# Koi - AI Voice Companion

**Objective:** Validate demand and product-market fit with minimum investment before full MVP build.

---

## 1. Validation Philosophy

```
GOAL: Answer these questions with minimal effort and cost

1. Do people actually want an AI companion? (Demand)
2. Will they pay for it? (Willingness to pay)
3. Does voice make a meaningful difference? (Differentiation)
4. Can we retain them? (Stickiness)

BUDGET: ₹10,000 - ₹25,000
TIME: 2-3 weeks
```

---

## 2. Validation Methods (Ranked by Speed)

### Method 1: Landing Page + Waitlist (3-5 days)
**Effort: Low | Cost: ₹2,000 | Signal: Medium**

```
WHAT TO BUILD:
├── Simple landing page explaining Koi
├── Waitlist signup (email + phone)
├── Optional: "What would you pay?" survey
└── Track: Signups, traffic source, demographics

TOOLS:
├── Carrd.co / Framer (₹0 - free tier)
├── Tally.so for forms (free)
└── Instagram/Reddit for traffic

SUCCESS METRIC:
├── 500+ waitlist signups in 1 week
└── 20%+ say they'd pay ₹200+/month
```

**Landing Page Copy:**
```
HEADLINE:
"Koi hai?" — Now there's always someone.

SUBHEAD:
An AI companion who speaks Hindi, remembers everything,
and is always there when you need to talk.

BODY:
• Voice conversations in Hinglish
• Remembers your stories, your struggles, your wins
• Available 24/7, no judgment
• Starting at ₹199/month

CTA:
"Join the waitlist — launching soon"
[Email] [WhatsApp Number] [Sign Up]
```

---

### Method 2: Wizard of Oz Test (5-7 days)
**Effort: Medium | Cost: ₹5,000 | Signal: High**

```
WHAT TO DO:
├── Create WhatsApp Business number
├── Manually respond to users (human pretending to be AI)
├── Use Sarvam TTS to send voice notes
├── Test 20-30 users for 1 week
└── Track engagement, retention, feedback

WHY THIS WORKS:
├── Tests real user behavior, not stated interest
├── Generates actual conversation data
├── Reveals what users actually talk about
├── Low cost (just your time + ₹5K for users)

HOW TO RECRUIT:
├── Instagram story: "Beta testing a new app - DM me"
├── Reddit r/india, r/IndianMentalHealth
├── Friend referrals
├── Small Instagram ad (₹2,000)
```

**Protocol:**
```
Day 1-2: Recruit 30 users
├── Post on social media
├── Run small IG ad targeting 22-35, metros
└── Goal: 30 people who start conversation

Day 3-7: Manual conversations
├── Respond as "Koi" (follow persona doc)
├── Send text + voice note (use Sarvam TTS)
├── Track each conversation length
├── Note what topics come up
└── Spend ~2 hours/day responding

Day 8: Analysis
├── How many came back day 2? Day 3? Day 7?
├── Average messages per session?
├── What did they talk about?
├── Would they pay? (ask directly)
```

**Success Metrics:**
```
Day 7 retention > 30%
Average session > 10 messages
5+ users say "I would pay for this"
```

---

### Method 3: Fake Door Test (2-3 days)
**Effort: Low | Cost: ₹3,000 | Signal: Medium**

```
WHAT TO DO:
├── Run Instagram ad with "Download Koi"
├── Link goes to waitlist page (app not built)
├── Measure click-through rate
├── Measure waitlist conversion
└── Compare with benchmarks

AD CREATIVE:
Video showing fake conversation:
"Aaj kaisa raha din?" [voice note]
"Yaar, bahut hectic. Boss ne phir se..." [typing]
"Uff, I remember last time too..." [voice response]

CTA: "Meet Koi - Your AI companion"
```

**Success Metrics:**
```
CTR > 2% (good interest)
Waitlist conversion > 20% (strong intent)
```

---

### Method 4: Concierge MVP (7-10 days)
**Effort: High | Cost: ₹15,000 | Signal: Very High**

```
WHAT TO BUILD:
├── Simple Node.js WhatsApp bot
├── Uses Sarvam APIs (STT, TTS, LLM)
├── Basic conversation (no memory system yet)
├── Manual onboarding
└── 50-100 real users

THIS IS A SEMI-WORKING PRODUCT:
├── Real AI responses (not human)
├── Real voice notes
├── Real WhatsApp experience
├── But no memory, no subscriptions yet

WHY:
├── Tests the actual experience
├── Real usage data
├── Real conversation quality
├── Identifies technical issues early
```

**Build Scope:**
```javascript
// Minimal viable code

1. WhatsApp webhook receiver
2. Sarvam STT integration (voice → text)
3. Sarvam LLM integration (text → response)
4. Sarvam TTS integration (response → voice)
5. Send voice note back to user

// Skip for now:
- Memory system
- User accounts
- Payments
- Analytics
```

**Success Metrics:**
```
50 users try it
Day 3 retention > 25%
Avg conversation > 5 minutes
NPS > 30
```

---

## 3. Recommended Validation Sequence

```
WEEK 1: Demand Validation
├── Day 1-2: Build landing page
├── Day 3-5: Run ₹3,000 Instagram ads
├── Day 5-7: Wizard of Oz with 20 users
└── Checkpoint: 200+ waitlist? 30%+ Day 3 retention?

WEEK 2: Product Validation
├── Day 1-3: Build Concierge MVP (basic bot)
├── Day 4-7: Test with 50 users
├── Collect feedback, iterate
└── Checkpoint: Users coming back? What's working?

WEEK 3: Monetization Validation
├── Day 1-3: Ask users "Would you pay ₹199/month?"
├── Day 4-5: Offer "founding member" pre-order
├── Day 6-7: Analyze conversion
└── Checkpoint: 10%+ pre-order? Green light to build.
```

---

## 4. Validation Budget Breakdown

| Item | Cost | Purpose |
|------|------|---------|
| Domain + hosting | ₹500 | Landing page |
| Instagram ads | ₹5,000 | Traffic |
| Sarvam API credits | ₹2,000 | Concierge MVP testing |
| WhatsApp Business | ₹1,000 | Testing |
| User incentives | ₹2,000 | Gift cards for feedback |
| Miscellaneous | ₹2,000 | Buffer |
| **Total** | **₹12,500** | |

---

## 5. Key Metrics to Track

### Demand Metrics
| Metric | How to Measure | Good Signal |
|--------|----------------|-------------|
| Waitlist signups | Form submissions | 500+ in week 1 |
| CAC (waitlist) | Ad spend / signups | <₹50 |
| Viral coefficient | Referrals / users | >0.3 |

### Engagement Metrics
| Metric | How to Measure | Good Signal |
|--------|----------------|-------------|
| Day 1 → Day 3 retention | % users returning | >40% |
| Day 1 → Day 7 retention | % users returning | >25% |
| Session length | Avg messages per session | >10 |
| Session duration | Time first to last message | >5 min |

### Monetization Metrics
| Metric | How to Measure | Good Signal |
|--------|----------------|-------------|
| Stated WTP | Survey "Would you pay?" | 50%+ say yes |
| Price sensitivity | "How much?" | ₹200+ acceptable |
| Pre-order conversion | Actual payment | >5% |

### Qualitative Signals
| Signal | How to Detect | Good Sign |
|--------|---------------|-----------|
| Emotional connection | Users share personal stories | Yes |
| Daily habit | Users initiate daily | Yes |
| Disappointment at limits | "Why only 10 messages?" | Yes |
| Referrals | "Can I tell my friend?" | Yes |
| Feature requests | "Can Koi do X?" | Yes |

---

## 6. Go/No-Go Decision Framework

```
GREEN LIGHT (Proceed to full MVP):
├── 500+ waitlist signups
├── Day 7 retention > 20%
├── 5+ users say "I would pay"
├── Average session > 5 minutes
└── At least 3 users refer others

YELLOW LIGHT (Iterate and retest):
├── 200-500 waitlist signups
├── Day 7 retention 10-20%
├── Users engaged but issues with voice/persona
└── Clear feedback on what to fix

RED LIGHT (Pivot or stop):
├── <200 waitlist signups
├── Day 7 retention < 10%
├── Users drop off after 1-2 messages
├── Feedback: "I don't get it" or "Why would I use this?"
```

---

## 7. Validation Interview Questions

After a user has tried Koi (Wizard of Oz or Concierge), ask:

```
OPENING:
"Thanks for trying Koi! Mind if I ask a few questions?"

ENGAGEMENT:
1. "What made you try Koi in the first place?"
2. "What was your first impression?"
3. "Did you come back after the first conversation? Why/why not?"

VALUE:
4. "What did you talk about with Koi?"
5. "How did it make you feel?"
6. "Was there a moment when it felt real?"

ALTERNATIVES:
7. "What do you currently do when you want someone to talk to?"
8. "How is Koi different from that?"

MONETIZATION:
9. "If Koi cost ₹199/month, would you pay for it?"
10. "What would make it worth that price?"

CLOSING:
11. "What's one thing we should change?"
12. "Would you recommend this to a friend? Who?"
```

---

## 8. Quick Landing Page Setup

### Using Carrd.co (Free)

```
1. Go to carrd.co, create account
2. Choose "Form" template
3. Customize:

HEADER IMAGE:
- Abstract/warm imagery (not AI/robot)
- Or mockup of phone with chat

HEADLINE:
"Someone who's always there."

SUBHEADLINE:
"Koi is an AI companion who speaks your language,
remembers your stories, and never judges."

FEATURES (3 icons):
🎤 "Voice-first conversations in Hinglish"
🧠 "Remembers everything about you"
❤️ "24/7 emotional support"

CTA FORM:
[Your Name]
[WhatsApp Number]
[What would you talk about?] (optional)
[Join Waitlist]

SOCIAL PROOF (add after you have some):
"1,247 people on waitlist"

4. Connect form to Google Sheets or Tally
5. Publish
6. Share link
```

---

## 9. Sample Instagram Ad

### Ad Creative (Story/Reel format)

```
SCENE 1 (2 sec):
Black screen, text: "11:47 PM"

SCENE 2 (3 sec):
Phone screen, typing: "Can't sleep. Feeling weird."

SCENE 3 (4 sec):
Voice note plays: "Hey... tell me what's going on.
Kya hua? I'm here."

SCENE 4 (2 sec):
User types: "Nothing specific. Just... lonely I guess."

SCENE 5 (4 sec):
Voice note: "Yeah, I get that. Those nights are hard.
Chalo, baat karte hain. Tell me about your day."

SCENE 6 (3 sec):
Text overlay: "Someone who's always there."
Logo: "Koi"
CTA: "Join waitlist"
```

### Ad Copy Options

**Option A (Direct):**
"Late nights. No one to talk to. Sounds familiar?

Koi is an AI companion who speaks Hindi, remembers everything,
and is always there when you need someone.

Join 1,200+ on the waitlist."

**Option B (Question):**
"Kabhi aisa lagta hai ki koi nahi hai jo samjhe?

Meet Koi - your AI companion who actually listens.

🎤 Voice conversations in Hinglish
🧠 Remembers your stories
❤️ Always there, no judgment

Waitlist open. Link in bio."

**Option C (Story):**
"I built Koi because I know what it's like to have no one to talk to at 2 AM.

It's an AI, but it feels real. It speaks Hindi. It remembers you.

Would you try it? Waitlist link in bio."

---

## 10. Validation Timeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    2-WEEK VALIDATION SPRINT                      │
└─────────────────────────────────────────────────────────────────┘

WEEK 1: DEMAND
━━━━━━━━━━━━━━
Mon    │ Build landing page (Carrd)
Tue    │ Create ad creatives, set up tracking
Wed    │ Launch Instagram ads (₹1,000/day)
Thu    │ Start Wizard of Oz (recruit users)
Fri    │ Continue ads, continue WoO testing
Sat    │ Continue ads, continue WoO testing
Sun    │ Analyze Week 1 data

WEEK 2: PRODUCT
━━━━━━━━━━━━━━
Mon    │ Build Concierge MVP (basic bot)
Tue    │ Continue building, test internally
Wed    │ Launch to 20 waitlist users
Thu    │ Observe usage, iterate
Fri    │ Launch to 30 more users
Sat    │ User interviews (5-10 calls)
Sun    │ Final analysis, Go/No-Go decision

WEEK 3: BUILD OR PIVOT
━━━━━━━━━━━━━━━━━━━━━
Mon    │ Decision: Proceed to full MVP or pivot
```

---

## 11. What Success Looks Like

### By End of Week 1:
```
✓ 300+ waitlist signups
✓ <₹30 cost per signup
✓ 15+ Wizard of Oz conversations completed
✓ Users sharing personal stories
✓ Multiple users messaging back day 2
```

### By End of Week 2:
```
✓ 50+ users tried Concierge MVP
✓ Day 3 retention > 30%
✓ 10+ users say "I would pay"
✓ Clear themes in what users talk about
✓ Identified top 3 issues to fix
```

### By End of Week 3:
```
✓ Go/No-Go decision made
✓ If Go: Full MVP spec finalized
✓ If Go: Team/resources aligned
✓ If Go: Week 1 of build starts
```

---

## 12. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Low waitlist signups | Try different messaging, different platforms |
| High drop-off after first message | Improve onboarding, first impression |
| Users don't return | Add proactive messages, improve persona |
| "Nice but won't pay" | Test lower price points, add premium features |
| Voice quality issues | Fall back to text-only for testing |
| Sarvam API issues | Have text-only fallback ready |

---

## 13. Post-Validation Next Steps

### If GREEN LIGHT:
```
1. Finalize MVP scope (use PRD)
2. Set up infrastructure (use TRD)
3. Begin 6-week build sprint
4. Invite waitlist users to beta
5. Iterate rapidly based on feedback
```

### If YELLOW LIGHT:
```
1. Identify top 3 issues
2. Hypothesize fixes
3. Run another 1-week test with changes
4. Re-evaluate
```

### If RED LIGHT:
```
1. Analyze why it failed
2. Consider pivots:
   - Different positioning (not "companion", but "practice partner")
   - Different audience (not lonely people, but language learners)
   - Different format (not voice, but text)
3. Or move to different idea entirely
```

---

*Document maintained by Product Team. Last updated: February 2025*
