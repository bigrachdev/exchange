"""
External Pinger - Deploy this on a different free service (Replit, PythonAnywhere, etc.)
This provides external pinging in addition to internal self-ping

Deploy on: Replit.com (free) or PythonAnywhere.com (free)
"""
import requests
import time
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ✅ CONFIGURE THIS - Your Render bot URL
BOT_URL = "https://exchange-1-0l54.onrender.com"  # ⚠️ CHANGE THIS!
PING_INTERVAL = 480  # 8 minutes (well before 15 min timeout)

def ping_bot():
    """Ping the bot to keep it alive"""
    endpoints = [
        f"{BOT_URL}/health",
        f"{BOT_URL}/",
    ]

    for endpoint in endpoints:
        try:
            logger.info(f"🏓 Pinging {endpoint}")
            response = requests.get(endpoint, timeout=10)

            if response.status_code == 200:
                logger.info(f"✅ Ping SUCCESS - {endpoint} - Status: {response.status_code}")
                return True
            else:
                logger.warning(f"⚠️ Ping returned {response.status_code} - {endpoint}")

        except requests.exceptions.Timeout:
            logger.error(f"❌ Ping TIMEOUT - {endpoint}")

        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Connection ERROR - {endpoint}")

        except Exception as e:
            logger.error(f"❌ Ping FAILED - {endpoint} - Error: {e}")

    return False

def main():
    """Main pinger loop"""
    logger.info("🚀 External Pinger Started")
    logger.info(f"🎯 Target: {BOT_URL}")
    logger.info(f"⏰ Interval: Every {PING_INTERVAL // 60} minutes")
    logger.info("=" * 50)

    ping_count = 0

    # Wait 10 seconds before first ping
    time.sleep(10)

    while True:
        try:
            ping_count += 1
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            logger.info(f"\n🔄 Ping #{ping_count} at {current_time}")

            success = ping_bot()

            if success:
                logger.info(f"✅ Ping #{ping_count} completed successfully")
            else:
                logger.error(f"❌ Ping #{ping_count} failed on all endpoints!")
                logger.error("🚨 Bot might be down! Check Render dashboard!")

            # Calculate next ping time
            next_ping = datetime.now().timestamp() + PING_INTERVAL
            next_ping_str = datetime.fromtimestamp(next_ping).strftime('%H:%M:%S')

            logger.info(f"⏰ Next ping at {next_ping_str}")
            logger.info("=" * 50)

            # Wait before next ping
            time.sleep(PING_INTERVAL)

        except KeyboardInterrupt:
            logger.info("\n👋 Pinger stopped by user")
            break

        except Exception as e:
            logger.error(f"💥 Error in main loop: {e}")
            logger.info("⏳ Waiting 60s before retry...")
            time.sleep(60)

if __name__ == "__main__":
    # Validate configuration
    if "YOUR-SERVICE-NAME" in BOT_URL:
        print("=" * 60)
        print("❌ ERROR: You must configure BOT_URL first!")
        print("=" * 60)
        print("\nEdit this file and change:")
        print('BOT_URL = "https://exchange-1-0l54.onrender.com"')
        print("\nTo your actual Render URL:")
        print('BOT_URL = "https://exchange-1-0l54.onrender.com"')
        print("=" * 60)
        exit(1)

    main()