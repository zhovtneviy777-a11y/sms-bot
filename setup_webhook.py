import requests

# Замініть на ваш токен
BOT_TOKEN = "6543217890:AAHdGvP9bQwVcXzZYL8kKmNt8rQpLmNoJKl"
WEBHOOK_URL = "https://sms-bot-production-4260.up.railway.app/webhook"

print("Setting webhook...")
response = requests.post(
    f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook",
    json={
        "url": WEBHOOK_URL,
        "drop_pending_updates": True,
        "allowed_updates": ["message", "callback_query"]
    }
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
