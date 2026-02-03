import schedule
import time
import requests
from datetime import datetime

def create_backup():
    """Trigger backup via API"""
    try:
        response = requests.post('http://localhost:5000/api/backup-database')
        if response.status_code == 200:
            print(f"[{datetime.now()}] Backup created successfully")
        else:
            print(f"[{datetime.now()}] Backup failed: {response.text}")
    except Exception as e:
        print(f"[{datetime.now()}] Backup error: {e}")

# Schedule daily backup at 2 AM
schedule.every().day.at("02:00").do(create_backup)

if __name__ == "__main__":
    print("Backup scheduler started...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute