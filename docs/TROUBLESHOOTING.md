# Koi Troubleshooting Guide

Common issues and how to fix them.

---

## Voice Agent Issues

### Agent Not Responding

**Symptoms:** You speak into the app but Koi does not respond. No audio comes back.

**Possible Causes and Solutions:**

1. **Agent is not running**
   - Check if the agent process is running: `ps aux | grep main.py`
   - Start it: `cd ~/koi-app/agent && poetry run python src/main.py dev`
   - Check agent logs for errors

2. **Sarvam API key is invalid or expired**
   - Check `.env` file: `SARVAM_API_KEY` must be set
   - Test the key: `curl -H "api-subscription-key: YOUR_KEY" https://api.sarvam.ai/health`
   - If expired, generate a new one at [sarvam.ai](https://www.sarvam.ai)

3. **LiveKit connection failed**
   - Verify `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` in `.env`
   - Check LiveKit dashboard for active rooms
   - Test with the [LiveKit Playground](https://agents-playground.livekit.io)

4. **Network issue**
   - Agent needs outbound HTTPS access to Sarvam and LiveKit APIs
   - Check if you are behind a VPN or firewall that blocks WebSocket connections

---

### No Audio Output (Agent Responds But No Sound)

**Symptoms:** You can see in logs that the agent is processing, but no audio plays on the phone.

**Solutions:**

1. **Check phone volume** -- make sure it is not muted or on silent
2. **Check audio route** -- make sure audio is going to speaker, not Bluetooth
3. **TTS failure** -- check agent logs for TTS-related errors. The Sarvam TTS endpoint might be rate-limited
4. **LiveKit audio track** -- the agent must publish an audio track. Check LiveKit dashboard for track status

---

### High Latency (Slow Responses)

**Symptoms:** Koi responds but takes more than 3 seconds.

**Solutions:**

1. **Check network latency** to Sarvam API:
   ```bash
   curl -o /dev/null -s -w "%{time_total}" https://api.sarvam.ai/health
   ```
   Should be under 500ms from India.

2. **Check STT processing time** in agent logs. If STT is slow, the audio might be too long -- check VAD sensitivity

3. **Check LLM response time** in agent logs. If the system prompt is too long, it slows down generation. Keep it under 2000 tokens

4. **Check TTS processing time** in agent logs. Long responses take longer to synthesize. Keep LLM max_tokens at 300

---

### Agent Crashes During Conversation

**Symptoms:** Agent process dies mid-conversation.

**Solutions:**

1. **Check for unhandled exceptions** in the agent logs
2. **Memory issue** -- check if the process is running out of memory: `top -l 1 | grep python`
3. **Connection timeout** -- if Sarvam APIs are unreachable for extended periods, the retry logic might exhaust. Check network stability
4. **Restart the agent** -- `cd ~/koi-app/agent && poetry run python src/main.py dev`

---

## Mobile App Issues

### OTP Not Received

**Symptoms:** After entering phone number, the OTP SMS never arrives.

**Solutions:**

1. **Check phone number format** -- must include country code (+91 for India)
2. **Check Supabase Auth settings:**
   - Go to Supabase Dashboard > Authentication > Providers > Phone
   - Verify Phone provider is enabled
   - Check rate limits (default: 5 per hour per phone)
3. **Check SMS provider** -- Supabase uses Twilio by default. Verify Twilio is configured and funded
4. **Wait and retry** -- some SMS providers have delays. Wait 60 seconds before requesting a new OTP
5. **Check spam filters** -- some phones filter SMS from unknown senders

---

### App Crashes on Launch

**Symptoms:** The app closes immediately after opening.

**Solutions:**

1. **Clear Expo cache:**
   ```bash
   cd ~/koi-app/mobile/KoiApp
   npx expo start --clear
   ```

2. **Reinstall dependencies:**
   ```bash
   rm -rf node_modules
   npm install
   ```

3. **Check for TypeScript errors:**
   ```bash
   npx tsc --noEmit
   ```

4. **Check minimum iOS version** -- Koi requires iOS 15+

---

### Microphone Permission Not Working

**Symptoms:** App does not ask for microphone permission, or permission is denied.

**Solutions:**

1. **iOS Settings** -- Go to Settings > Privacy > Microphone > find Koi app > toggle ON
2. **Check app.json** -- verify `NSMicrophoneUsageDescription` is set in the iOS config
3. **Reset permissions** -- delete the app and reinstall
4. **Simulator limitation** -- microphone does not work in iOS simulator. Use a physical device

---

### Connection Failed (Cannot Start Conversation)

**Symptoms:** Tapping "Start Talking" shows a connection error.

**Solutions:**

1. **Check internet connection** -- WiFi or cellular must be working
2. **Check Supabase Edge Function:**
   - The `generate-room-token` function must be deployed
   - Check Supabase Dashboard > Edge Functions > Logs
3. **Check LiveKit URL** -- verify `LIVEKIT_URL` in the edge function environment variables
4. **Check authentication** -- you must be logged in. If the auth token expired, log out and log back in
5. **Check CORS** -- if running locally, Supabase Edge Functions need proper CORS headers

---

### VoiceOrb Animation Lag

**Symptoms:** The orb animation stutters or is not smooth.

**Solutions:**

1. **Enable Hermes engine** -- verify it is enabled in app.json (should be by default in Expo SDK 50+)
2. **Check for JS thread blocking** -- heavy synchronous operations can block the UI thread
3. **Use `react-native-reanimated`** -- animations should run on the UI thread, not the JS thread
4. **Test on device** -- simulators can have different performance characteristics

---

## Database Issues

### User Profile Not Created After Signup

**Symptoms:** User signs up but their profile is empty or missing.

**Solutions:**

1. **Check the trigger** -- the `handle_new_user` function must be set up:
   ```sql
   SELECT * FROM pg_trigger WHERE tgname = 'on_auth_user_created';
   ```
2. **Run the migration** -- make sure `001_create_tables.sql` has been executed
3. **Check RLS policies** -- the user must be able to read their own profile

---

### Data Not Appearing in Dashboard

**Symptoms:** Conversations happen but nothing shows up in the Supabase table viewer.

**Solutions:**

1. **Check the `SUPABASE_DB_URL`** -- the agent connects directly to PostgreSQL, not through the Supabase API. Verify the connection string
2. **Check RLS** -- if using the Supabase dashboard, you are viewing as a service role. Data should be visible. If using the API, check that the user's JWT matches the RLS policy
3. **Check agent logs** -- look for database insert errors

---

## Test Issues

### Tests Fail With Import Errors

**Symptoms:** `ModuleNotFoundError: No module named 'src'`

**Solutions:**

```bash
cd ~/koi-app/agent
# Make sure you are running tests through Poetry
poetry run pytest

# If the src package is not found, check pyproject.toml packages config
# It should have: packages = [{include = "src"}]
```

### Tests Fail With Async Errors

**Symptoms:** `RuntimeError: no current event loop` or `PytestUnraisableExceptionWarning`

**Solutions:**

- Verify `asyncio_mode = "auto"` in `pyproject.toml` under `[tool.pytest.ini_options]`
- Make sure `pytest-asyncio >= 0.23` is installed
- Use `@pytest.mark.asyncio` on all async test functions

---

## Still Stuck?

1. **Check the logs** -- the answer is almost always in the logs
2. **Search existing issues** on the GitLab repository
3. **Ask in the team channel** with:
   - What you were trying to do
   - What happened instead
   - Relevant log output
   - Steps to reproduce
