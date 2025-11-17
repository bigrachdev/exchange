# instance_lock.py - Prevent multiple bot instances

import os
import sys
import time
import logging

LOCK_FILE = "/tmp/bot_instance.lock"

def acquire_lock():
    """Ensure only one instance is running"""
    if os.path.exists(LOCK_FILE):
        # Check if lock is stale (older than 5 minutes)
        try:
            lock_age = time.time() - os.path.getmtime(LOCK_FILE)
            if lock_age < 300:  # 5 minutes
                logging.error("❌ Another bot instance is already running!")
                logging.error(f"Lock file: {LOCK_FILE}")
                logging.error("If you're sure no other instance is running, delete the lock file:")
                logging.error(f"rm {LOCK_FILE}")
                sys.exit(1)
            else:
                logging.warning("⚠️ Stale lock detected, removing...")
                os.remove(LOCK_FILE)
        except Exception as e:
            logging.error(f"Error checking lock: {e}")
    
    # Create lock file
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        logging.info(f"✅ Instance lock acquired: {LOCK_FILE}")
    except Exception as e:
        logging.error(f"Failed to create lock: {e}")

def release_lock():
    """Release the instance lock"""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
            logging.info("✅ Instance lock released")
    except Exception as e:
        logging.error(f"Error releasing lock: {e}")