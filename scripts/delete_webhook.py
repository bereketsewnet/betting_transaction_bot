"""Script to delete Telegram webhook (legacy - use manage_webhook.py instead)."""
import asyncio
import sys
from scripts.manage_webhook import delete_webhook

# For backward compatibility
if __name__ == "__main__":
    print("⚠️  Note: This script is deprecated. Use 'python scripts/manage_webhook.py delete' instead.")
    success = asyncio.run(delete_webhook())
    sys.exit(0 if success else 1)

