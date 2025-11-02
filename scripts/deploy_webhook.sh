#!/bin/bash
# Script to set up Telegram webhook

# Configuration
BOT_TOKEN="${TELEGRAM_BOT_TOKEN}"
WEBHOOK_URL="${WEBHOOK_URL}"
SECRET_TOKEN="${WEBHOOK_SECRET_TOKEN}"

if [ -z "$BOT_TOKEN" ] || [ -z "$WEBHOOK_URL" ]; then
    echo "Error: TELEGRAM_BOT_TOKEN and WEBHOOK_URL must be set"
    exit 1
fi

# Set webhook
echo "Setting webhook..."
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
    -H "Content-Type: application/json" \
    -d "{
        \"url\": \"${WEBHOOK_URL}\",
        \"secret_token\": \"${SECRET_TOKEN}\",
        \"drop_pending_updates\": true
    }"

echo ""
echo "Webhook set successfully!"
echo "Webhook URL: ${WEBHOOK_URL}"

# Get webhook info
echo ""
echo "Webhook info:"
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"

