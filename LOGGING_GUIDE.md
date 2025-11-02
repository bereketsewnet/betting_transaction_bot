# Bot Logging Guide

## Overview
The bot now has comprehensive emoji-based logging to track every step of user interactions.

## Emoji Reference

| Emoji | Meaning | Where Used |
|-------|---------|-----------|
| 📧 | Email input | Login & Registration |
| 🔐 | Password processing | Login & Registration |
| 👤 | Display name | Registration |
| 📱 | Phone number | Registration |
| 🔄 | API calls | All API interactions |
| 📊 | State data | FSM state dumps |
| ✅ | Success | Validation passed, API success |
| ❌ | Errors | Validation failed, API errors |
| ⏭️ | Skip actions | Optional fields |
| 🌐 | API requests | HTTP requests |
| 📡 | API responses | HTTP responses |

## Example Log Output

### Successful Login Flow
```
INFO     User 123456 started login
INFO     📧 User 123456 entered username for login
INFO     ✅ Username saved for user 123456, requesting password
INFO     🔐 Login password handler triggered for user 123456
INFO        State: LoginStates:waiting_for_password
INFO     📊 State data for user 123456: ['username']
INFO     🔄 Processing login for user 123456 with username player3@example.com
INFO     🌐 API Request: POST http://localhost:3000/api/v1/auth/login
INFO     📡 API Response: POST http://localhost:3000/api/v1/auth/login - Status: 200
INFO     ✅ Registration successful for user 123456, playerUuid: abc-123
```

### Failed Validation
```
INFO     📧 User 123456 entered email for registration
WARNING  ❌ Invalid email from user 123456: Email format is invalid
```

### Registration Flow
```
INFO     User 123456 started registration
INFO     📧 User 123456 entered email for registration
INFO     ✅ Valid email for user 123456, requesting password
INFO     🔐 User 123456 entered password for registration
INFO     ✅ Valid password for user 123456, requesting display name
INFO     👤 User 123456 entered display name for registration
INFO     ✅ Valid display name for user 123456, requesting phone
INFO     📱 User 123456 processing phone number
INFO     ⏭️ User 123456 skipped phone number
INFO     📊 Registration data for user 123456:
INFO        Email/Username: player@example.com
INFO        Display Name: John Doe
INFO        Phone: None
INFO     🔄 Calling register_player API for user 123456
INFO     ✅ Registration successful for user 123456, playerUuid: xyz-789
```

## Key Changes

### Registration
- **Before**: Username → Email → Password (6+ chars)
- **After**: Email → Password (8+ chars) → Display Name → Phone
- **Note**: Email is used as BOTH username and email in API calls

### Login
- **Before**: Username → Password
- **After**: Email → Password (8+ chars)
- **Note**: Email is sent as username to API

### Password Validation
- **Minimum length**: 8 characters (was 6)
- **Applied to**: Both login and registration
- **Error message**: "❌ Password must be at least 8 characters"

## Debugging Tips

1. **Bot stops after entering password?**
   - Look for: `🔐 Login password handler triggered`
   - If not present: Handler not called (middleware issue)
   - If present: Check next log line for error

2. **API calls failing?**
   - Look for: `🌐 API Request:` followed by `📡 API Response:`
   - Check status code in response
   - Look for `❌ API Error` for details

3. **State issues?**
   - Look for: `📊 State data for user X:`
   - Check if expected data is present
   - Look for `❌ No username in state data` errors

4. **Registration not completing?**
   - Follow the emoji trail: 📧 → 🔐 → 👤 → 📱 → 🔄
   - If it stops at any point, previous step had an error

## Common Issues

### Issue: Password handler not triggered
**Symptoms**: Logs show `✅ Username saved` but no `🔐 Login password handler triggered`

**Causes**:
- Middleware not injecting dependencies
- FSM state not set correctly
- Handler filter not matching

**Solution**: Check logs for middleware execution and state transitions

### Issue: API returns 401
**Symptoms**: `📡 API Response: ... - Status: 401`

**Causes**:
- Invalid credentials
- API not allowing requests from bot's host

**Solution**: 
1. Check credentials match API database
2. Verify API CORS/whitelist settings

### Issue: "Session expired" error
**Symptoms**: `❌ No username in state data`

**Causes**:
- FSM state cleared unexpectedly
- Bot restarted during conversation
- State storage issue

**Solution**: User should restart with `/start`

