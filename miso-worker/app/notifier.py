import requests
import logging
import os
import sys
import json

# CONFIG
# Replace with your actual webhook URL if you have it. 
# Otherwise, it defaults to None and logs to stdout.
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK", "")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [NOTIFIER] %(message)s', stream=sys.stdout)
logger = logging.getLogger(__name__)

class Notifier:
    def send_alert(self, message):
        # 1. Always log locally
        logger.info(f"📢 ALERT TRIGGERED: {message}")
        
        # 2. Push to Discord (if configured)
        if DISCORD_WEBHOOK and "http" in DISCORD_WEBHOOK:
            try:
                payload = {
                    "content": f"🤖 **MISO WATCHDOG:** {message}",
                    "username": "MISO Sentinel"
                }
                resp = requests.post(DISCORD_WEBHOOK, json=payload)
                if resp.status_code == 204:
                    logger.info("✅ Alert sent to Discord.")
                else:
                    logger.error(f"Discord Error: {resp.status_code}")
            except Exception as e:
                logger.error(f"Network Fail: {e}")
        else:
            logger.warning("⚠️ No Discord Webhook found. Alert is local only.")

if __name__ == "__main__":
    n = Notifier()
    n.send_alert("System Test: MISO Voice Module is Active.")
