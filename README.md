# Betting Transaction Bot

Production-ready Telegram bot built with **aiogram v3** for managing betting payment transactions. This bot integrates with the Betting Payment Manager REST API to handle deposits, withdrawals, and transaction history.

## Features

- 🎯 **Complete Transaction Management**: Deposit and withdrawal flows with FSM (Finite State Machine)
- 🌍 **Multi-language Support**: Language selection from API configuration
- 👤 **User Authentication**: Register, login, or continue as guest
- 📸 **File Upload**: Screenshot upload support for transaction verification
- 📜 **Transaction History**: View and manage transaction history
- 🔔 **Notifications**: Real-time notifications from backend
- 🚀 **Production Ready**: Supports both polling and webhook modes
- 💾 **Persistent Storage**: SQLite storage (no Redis required)

## Project Structure

```
betting_transaction_bot/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── bot.py                 # Main bot file (polling/webhook)
│   ├── logger.py              # Logging configuration
│   ├── handlers/              # Bot handlers
│   │   ├── start.py           # Start command handler
│   │   ├── main_menu.py       # Main menu handler
│   │   ├── deposit_flow.py    # Deposit transaction flow
│   │   ├── withdraw_flow.py   # Withdrawal transaction flow
│   │   ├── history.py          # Transaction history
│   │   ├── inline_lists.py     # Inline list pagination
│   │   └── callbacks.py        # Callback handlers
│   ├── services/               # Business logic services
│   │   ├── api_client.py      # HTTP client for API
│   │   ├── player_service.py  # Player management
│   │   ├── file_service.py    # File upload/download
│   │   └── notify_service.py   # Notification handling
│   ├── middlewares/            # Bot middlewares
│   │   ├── throttling.py       # Rate limiting
│   │   └── error_handler.py   # Error handling
│   ├── storage/                # Storage abstraction
│   │   ├── sqlite_storage.py   # SQLite implementation
│   │   └── memory_storage.py   # In-memory (dev only)
│   ├── utils/                  # Utilities
│   │   ├── keyboards.py        # Keyboard builders
│   │   ├── validators.py       # Input validation
│   │   └── text_templates.py   # Text templates
│   └── schemas/                # Pydantic models
│       └── api_models.py       # API request/response models
├── tests/                      # Test suite
├── scripts/                    # Deployment scripts
│   └── deploy_webhook.sh       # Webhook setup script
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── pytest.ini                 # Pytest configuration
├── pyproject.toml             # Linting configuration
└── README.md                   # This file
```

## Requirements

- Python 3.10+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Betting Payment Manager API (backend service)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd betting_transaction_bot
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Configuration

Create a `.env` file with the following variables:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here

# API Configuration
API_BASE_URL=http://localhost:3000/api/v1

# Webhook Configuration (for production)
USE_WEBHOOK=false
WEBHOOK_URL=https://your-domain.com/webhook
WEBHOOK_SECRET_TOKEN=your_webhook_secret

# Backend Integration
BACKEND_NOTIFY_SECRET=your_backend_secret

# Storage Configuration
STORAGE_MODE=sqlite  # sqlite or memory
DB_PATH=./data/bot.sqlite

# File Upload Configuration
MAX_UPLOAD_MB=5

# Application Configuration (for webhook mode)
APP_HOST=0.0.0.0
APP_PORT=8443

# Admin Configuration
BOT_ADMIN_CHAT_ID=your_admin_chat_id

# Logging
LOG_LEVEL=INFO

# Web App URL (for MiniApp redirect)
WEB_APP_URL=https://your-web-app.com
```

## Running the Bot

### Development Mode (Polling)

Run the bot in polling mode for local development:

```bash
python -m app.bot --mode polling
```

Or use the module directly:

```bash
python -m app
```

### Production Mode (Webhook)

1. **Set up webhook** (using provided script):

   ```bash
   export TELEGRAM_BOT_TOKEN=your_token
   export WEBHOOK_URL=https://your-domain.com/webhook
   export WEBHOOK_SECRET_TOKEN=your_secret
   bash scripts/deploy_webhook.sh
   ```

2. **Run bot with webhook**:

   ```bash
   python -m app.bot --mode webhook
   ```

## Deployment Examples

### Using ngrok (for testing)

1. **Install ngrok**: Download from [ngrok.com](https://ngrok.com/)

2. **Expose local server**:
   ```bash
   ngrok http 8443
   ```

3. **Update webhook URL** in `.env` with ngrok URL:
   ```env
   WEBHOOK_URL=https://your-ngrok-url.ngrok.io/webhook
   ```

4. **Run bot**:
   ```bash
   python -m app.bot --mode webhook
   ```

### Production Deployment (Nginx + systemd)

1. **Create systemd service** (`/etc/systemd/system/betting-bot.service`):
   ```ini
   [Unit]
   Description=Betting Transaction Bot
   After=network.target

   [Service]
   Type=simple
   User=your-user
   WorkingDirectory=/path/to/betting_transaction_bot
   Environment="PATH=/path/to/venv/bin"
   ExecStart=/path/to/venv/bin/python -m app.bot --mode webhook
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

2. **Nginx configuration** (`/etc/nginx/sites-available/betting-bot`):
   ```nginx
   server {
       listen 443 ssl;
       server_name your-domain.com;

       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;

       location /webhook {
           proxy_pass http://localhost:8443/webhook;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }

       location /notify {
           proxy_pass http://localhost:8443/notify;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-BACKEND-SECRET $http_x_backend_secret;
       }
   }
   ```

3. **Enable and start service**:
   ```bash
   sudo systemctl enable betting-bot
   sudo systemctl start betting-bot
   sudo systemctl status betting-bot
   ```

## Testing

Run tests with pytest:

```bash
pytest tests/ -v
```

Run with coverage:

```bash
pytest tests/ --cov=app --cov-report=html
```

## Linting

Format code with black:

```bash
black app/ tests/
```

Check code style with ruff:

```bash
ruff check app/ tests/
```

## API Integration

The bot integrates with the Betting Payment Manager API. Key endpoints used:

- `GET /config/languages` - Get available languages
- `GET /config/welcome?lang=<code>` - Get welcome message
- `GET /config/deposit-banks` - Get deposit banks
- `GET /config/withdrawal-banks` - Get withdrawal banks
- `GET /config/betting-sites` - Get betting sites
- `POST /players` - Create guest player
- `POST /players/register` - Register player
- `POST /transactions` - Create transaction (supports multipart/file upload)
- `GET /transactions?playerUuid=<uuid>` - Get transaction history
- `GET /transactions/:id` - Get transaction details
- `POST /uploads` - Upload file
- `GET /uploads/config` - Get upload configuration

## Backend Notifications

The bot exposes a `/notify` endpoint to receive notifications from the backend:

```bash
curl -X POST https://your-domain.com/notify \
  -H "Content-Type: application/json" \
  -H "X-BACKEND-SECRET: your_secret" \
  -d '{
    "playerUuid": "player-uuid",
    "transactionUuid": "tx-uuid",
    "status": "SUCCESS",
    "message": "Transaction completed successfully"
  }'
```

## Security Considerations

- ✅ Callback data validation to prevent injection
- ✅ Rate limiting (8 seconds between actions)
- ✅ Webhook secret token verification
- ✅ Backend notification secret verification
- ✅ File size and type validation
- ✅ Input validation for all user inputs

## Storage

The bot supports two storage modes:

1. **SQLite** (default, recommended for production):
   - Persistent storage
   - Player UUID mapping
   - FSM state management
   - Configured via `STORAGE_MODE=sqlite` and `DB_PATH`

2. **Memory** (for development only):
   - Ephemeral storage (data lost on restart)
   - Configured via `STORAGE_MODE=memory`
   - ⚠️ **Warning**: Not suitable for production!

## Troubleshooting

### Bot not responding

1. Check bot token in `.env`
2. Verify API base URL is accessible
3. Check logs for errors

### Webhook not working

1. Verify webhook URL is publicly accessible (HTTPS required)
2. Check webhook secret token matches
3. Use `scripts/deploy_webhook.sh` to reset webhook

### Transaction creation fails

1. Verify player UUID exists in storage
2. Check API endpoint is accessible
3. Verify file size and type if uploading screenshot

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

[Your License Here]

## Support

For issues and questions, please contact the development team or open an issue in the repository.

---

**Note**: This bot is production-ready but should be thoroughly tested in a staging environment before deploying to production.

