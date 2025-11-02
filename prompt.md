# Prompt: Generate a production-ready Telegram bot (Python, aiogram v3) — **NO Docker, NO Redis**

You are an expert Python backend engineer. Generate a **production-ready Telegram bot** project in **Python 3.10+** using **aiogram v3** that integrates with the provided Betting Payment Manager REST API. The generated project must be a complete repo scaffold (files, tests, `.env.example`, README) and implement the exact flows described below.

Important: use async patterns (asyncio + httpx), follow clean architecture, include comments and README with run/deploy steps, and make Redis **not required**. Use **SQLite (recommended)** or file-based fallback for persistent mappings and FSM storage. The bot must work in either long-polling mode (dev) or webhook mode (production). Provide tests with pytest + pytest-asyncio and a lint config (ruff + black or flake8 + black).

Refer to the provided backend API contract (examples) for exact shapes and endpoints (e.g. `POST /players`, `POST /transactions` with multipart/file upload, `GET /config/languages`, `GET /config/deposit-banks`). Use these endpoints as the authority for request/response formats. :contentReference[oaicite:2]{index=2} :contentReference[oaicite:3]{index=3}

---

### High-level functional requirements (must implement)

1. **Language & Welcome**
   - On `/start`, show a welcome message and present **language choices** from API: `GET /config/languages`. List languages as inline buttons (paginated if long).
   - Once user picks a language, fetch the welcome template from `GET /config/welcome?lang=<code>` and display it.
   - Persist the chosen language for the user (prefer backend `POST /players` to create/update player profile with `languageCode` and telegram identifiers). Use temporary `playerUuid` for guest flows as explained below.

2. **User identity: register / login / guest**
   - Provide three options after welcome: **Register**, **Login**, **Continue as Guest**.
   - **Register**: call `POST /players/register` with data (telegramId, telegramUsername, languageCode, username, email, password, displayName, phone). Handle validation errors (400) and conflict (409).
   - **Login**: if you support login via bot, implement a short flow to collect username & password, call `/auth/login` (if present in your API), store returned `playerUuid`/tokens as required. (If the API only supports web login, the bot should show a MiniApp/web link for full login.)
   - **Guest**: create a temporary player via `POST /players` (legacy create) which returns `player.playerUuid` (temporary). Use that `playerUuid` for subsequent transaction calls. The API supports temporary ID transactions lookup via `GET /transactions/temp?tempId=<tempId>`. Persist `playerUuid` in **SQLite** (or local mapping keyed by `telegram_id`) as the authoritative in-bot mapping.

   > Storage note: Redis is **not required**. Implement storage abstraction so implementers can plug in Redis later if desired. Default storage is:
   > - `storage/sqlite_storage.py` (recommended) — persistent mapping & FSM state
   > - `storage/memory_storage.py` — ephemeral for dev; warn in README that it's not persistent.

3. **Main menu & flows**
   - Main menu buttons: **Deposit**, **Withdraw**, **History**, **Open Web (MiniApp)**, **Help**.
   - **Deposit** flow (FSM):
     - Fetch deposit banks `GET /config/deposit-banks`. Show as inline buttons, use a reusable **paginated inline list** component (e.g., 6 items/page) with `Prev/Next`.
     - On bank select: show bank details (mask account number), ask amount (preset quick buttons + custom amount input), ask betting site selection `GET /config/betting-sites` (inline list), ask for `playerSiteId` (quick-reply presets or text small input), request screenshot upload (photo). Accept photo/file only (limit based on `GET /uploads/config`).
     - On confirm: upload screenshot to backend if provided (call `POST /uploads` or attach in multipart on `/transactions`), then call `POST /transactions` (multipart/form-data) with fields per API: `playerUuid`, `type=DEPOSIT`, `amount`, `currency`, `depositBankId`, `bettingSiteId`, `playerSiteId`, `screenshot` (file). Show created transaction summary & `transaction.transactionUuid`. `currency` always ETB.
   - **Withdraw** flow (FSM):
     - Fetch withdrawal banks `GET /config/withdrawal-banks`. For selected bank, read `requiredFields` (array) from the API and ask for them one-by-one (guided inputs), then amount, betting site & playerSiteId, screenshot if required. Confirm and call `POST /transactions` with `type=WITHDRAW`, `withdrawalBankId`, `withdrawalAddress` (or required fields), etc.
   - **History**:
     - Fetch `GET /transactions?playerUuid=<playerUuid>&page=1&limit=10`. Show last N entries as inline buttons; on selection show detailed transaction info `GET /transactions/:id?player_uuid=<playerUuid>` including screenshot link and status.

4. **Mini App redirect**
   - For users who prefer web UI, include a clear **Open Web App / MiniApp** button that opens the website URL (from a configurable env var). If the user is guest with temp `playerUuid`, append `?playerUuid=...` to the URL so the web app can show their transactions immediately.

5. **Notifications & Notify endpoint**
   - Implement a webhook `POST /notify` (or `app/notify`) in the bot to accept backend push notifications (admin/agent status updates). Secure that endpoint with a header `X-BACKEND-SECRET` (env var).
   - When backend notifies bot of a transaction update, the bot sends a message to the affected player (using stored `playerUuid` → telegram_id mapping) with updated status & optionally evidence link. Provide `notify_service.py` abstraction.

   > Deployment note: webhook mode requires a public HTTPS endpoint reachable by the backend; add examples using `ngrok`, or using a VPS + reverse proxy + TLS.

6. **File handling**
   - When user uploads a photo: bot downloads the file to temp, validate type & size (respect `GET /uploads/config`), and either:
     - Upload to backend `POST /uploads` returning a `file.url`, then include that url in `POST /transactions` JSON, **OR**
     - Submit the file as part of multipart `POST /transactions` (the API supports multipart upload). Use the multipart option if available; otherwise upload then POST JSON referencing `screenshotUrl`.
   - Delete temp files after upload. Retry once on transient failure.

7. **UX constraints (minimal typing)**
   - Use inline keyboards, reply keyboards, and single-field prompts — avoid free-form long text.
   - Use type validation (numeric amount, max lengths).
   - If user needs to enter text (playerSiteId or bank account), keep prompts short and validate.

8. **Inline paginated list helper**
   - Implement a reusable inline pagination helper for large lists (banks, betting sites, languages).
   - Callback data must be namespaced and validated (`bank:deposit:<id>`, `bank:withdraw:<id>`, `site:<id>`, `lang:<code>`).
   - Implement expiry: after X minutes edit message to show “Expired — reopen menu”.

9. **Rate limiting & security**
   - Throttle create-transaction actions (e.g., max 1 request per 8 seconds per user).
   - Secure webhook notify endpoint via `X-BACKEND-SECRET`.
   - Do not log secrets, access tokens or file contents.
   - Validate callback data to prevent injection.

10. **Storage & FSM**
    - Use a storage abstraction. Default, in order:
      1. `storage/sqlite_storage.py` — persistent mapping and FSM (recommended)
      2. `storage/memory_storage.py` — ephemeral for development. Document the risk (data lost on restart).
    - Persist mapping: `playerUuid` ↔ `telegram_id` in SQLite (or via `POST /players` updates) to support notify callbacks.

11. **Dev / Prod modes**
    - Long-polling CLI command: `python -m app.bot --mode polling`.
    - Webhook CLI command: `python -m app.bot --mode webhook`.
    - Provide `scripts/deploy_webhook.sh` helper for `setWebhook` including secret token (shows how to set webhook using Telegram `setWebhook` API).
    - Provide examples for deploying webhook behind TLS (ngrok + example, or systemd + reverse proxy).

12. **Testing & CI**
    - Provide pytest tests for:
      - api_client wrappers (mock httpx)
      - inline pagination logic
      - deposit FSM happy path (mocking Telegram updates and httpx)
    - Provide GitHub Actions workflow that runs lint + tests.

13. **(Removed) Docker & compose**
    - **This project does NOT require Docker.** Do not produce Dockerfile or docker-compose in the required deliverables.
    - Instead, provide clear local-run and deploy instructions: `python -m venv .venv && pip install -r requirements.txt`, environment variables, running in polling mode, and webhook deployment examples (ngrok or production instructions).

14. **.env.example** (required entries — updated for no-redis)
    - TELEGRAM_BOT_TOKEN
    - API_BASE_URL (e.g., http://localhost:3000/api/v1)
    - USE_WEBHOOK (true/false)
    - WEBHOOK_URL (if using webhook)
    - BACKEND_NOTIFY_SECRET
    - DB_PATH (e.g., ./data/bot.sqlite) — used for sqlite storage
    - STORAGE_MODE (options: sqlite|memory)
    - MAX_UPLOAD_MB (e.g., 5)
    - BOT_ADMIN_CHAT_ID
    - SENTRY_DSN (optional)
    - APP_HOST / APP_PORT (for webhook server binding)
    - LOG_LEVEL

15. **Project layout (must follow)**
Betting_transaction_bot/
├─ app/
│ ├─ init.py
│ ├─ config.py
│ ├─ bot.py
│ ├─ handlers/
│ │ ├─ start.py
│ │ ├─ main_menu.py
│ │ ├─ deposit_flow.py
│ │ ├─ withdraw_flow.py
│ │ ├─ history.py
│ │ ├─ inline_lists.py
│ │ └─ callbacks.py
│ ├─ services/
│ │ ├─ api_client.py # httpx async wrapper with typed methods for endpoints
│ │ ├─ player_service.py # create/get/update player profiles (POST /players, POST /players/register)
│ │ ├─ file_service.py # download file from Telegram, upload to backend
│ │ └─ notify_service.py # send messages & webhook notify endpoint
│ ├─ middlewares/
│ │ ├─ throttling.py
│ │ └─ error_handler.py
│ ├─ storage/
│ │ ├─ sqlite_storage.py # persistent mapping & FSM (default)
│ │ └─ memory_storage.py # ephemeral storage for dev
│ ├─ utils/
│ │ ├─ keyboards.py
│ │ ├─ text_templates.py # fetch templates by languageCode from /config/templates or /config/welcome
│ │ └─ validators.py
│ ├─ schemas/ # pydantic request/response models matching examples
│ └─ logger.py
├─ tests/
├─ scripts/
│ └─ deploy_webhook.sh
├─ requirements.txt
├─ .env.example
└─ README.md

16. **API Contracts to use (from provided examples)**
   - Create temporary/guest player: `POST /players` → returns `{ player.playerUuid }`. :contentReference[oaicite:4]{index=4}
   - Full player registration: `POST /players/register` for account creation. :contentReference[oaicite:5]{index=5}
   - Fetch languages: `GET /config/languages`. :contentReference[oaicite:6]{index=6}
   - Fetch welcome template: `GET /config/welcome?lang=<code>`. :contentReference[oaicite:7]{index=7}
   - Fetch deposit/withdraw banks: `GET /config/deposit-banks` and `GET /config/withdrawal-banks`. :contentReference[oaicite:8]{index=8}
   - Create transaction with file: `POST /transactions` (multipart/form-data) — example present in docs. Handle both JSON-only and multipart file submission. :contentReference[oaicite:9]{index=9}
   - Get player transactions: `GET /transactions?playerUuid=...` and temp lookup `GET /transactions/temp?tempId=...`. :contentReference[oaicite:10]{index=10}

17. **Deliverables**
   - A zipped repo scaffold (or repo) containing all code & config described above (no Docker artifacts).
   - README with local dev, webhook setup, how to connect backend notify to bot (example curl with `X-BACKEND-SECRET`), and how to use MiniApp redirect.
   - Tests and CI workflow.

---

### Edge-cases & implementation hints (in-prompt guidance for code gen)
- The bot MUST never require long free-text for bank selection or template selection — use inline keyboards with pagination.
- When backend returns `requiredFields` for withdrawal banks, map the fields to forms and validate them.
- Prefer `multipart` upload directly to `/transactions` if backend supports it (example exists), otherwise upload to `/uploads` then reference URL.
- Keep `playerUuid` authoritative for transactions — either from created player (registered or temp) or returned on login.
- Include TODO comments where backend behavior may vary (e.g., if refresh token flow is web-only).
- Implement careful callback data validation: limit length, whitelist characters `[a-z0-9:_-]`, and reject invalid patterns.
- Use `httpx.AsyncClient` with proper timeouts and retry/backoff for transient failures.
- When using SQLite, ensure DB access is async-safe (use `aiosqlite` or run blocking DB calls in threadpool). Document the choice.
- For file temp handling, use Python `tempfile` with `delete=False` then unlink after upload. Enforce `MAX_UPLOAD_MB`.

---

### Final instructions for generator:
- Produce a ready-to-run repository scaffold as described.
- Do **not** include Dockerfile or docker-compose files anywhere.
- Use **SQLite** as the default persistent storage option (configurable via `STORAGE_MODE`).
- Provide examples in README for both polling and webhook mode and examples for exposing the webhook (ngrok, systemd + Nginx).
- Provide tests & GitHub Actions CI (lint + test).
- Include clear TODOs where backend interaction choices can vary.
- Make sure the produced code runs with `python -m app.bot --mode polling` after installing `requirements.txt` and populating `.env`.

---

**Validation summary (explicit)**
- Removing Redis: replaced by SQLite & memory storage. This preserves persistence and supports notify callbacks without requiring Redis. If you later want Redis, implement a small adapter to the `storage` abstraction.
- Removing Docker: CI/tests and local dev will run natively. For production, deployment instructions included (systemd, nginx, uvicorn/hypercorn or run as system service).
- Ensure webhook functionality has TLS available — use ngrok or proper reverse proxy in README.

---

After starting the bot successfully, print a clear message like:
"✅ Bot is running at http://<server_ip_or_localhost>:<port>"
or if it’s deployed, "✅ Telegram bot running successfully at: <bot_url>".
This helps identify the exact URL or port the bot is accessible from.
