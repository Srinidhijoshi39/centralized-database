import os
import json
from datetime import datetime
from dotenv import load_dotenv
import psycopg2

load_dotenv()

class BackupManager:
    def __init__(self):
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_name = os.getenv('DB_NAME', 'trading_master_db')
        self.db_user = os.getenv('DB_USER', 'postgres')
        self.db_password = os.getenv('DB_PASSWORD')
        self.db_port = os.getenv('DB_PORT', '5432')
        self.backup_dir = os.getenv('BACKUP_DIR', './backups')
        
        os.makedirs(self.backup_dir, exist_ok=True)

    def create_backup(self):
        """Create database backup using Python"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"{self.backup_dir}/backup_{self.db_name}_{timestamp}.json"
        
        try:
            conn = psycopg2.connect(
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password,
                port=self.db_port
            )
            cur = conn.cursor()
            
            backup_data = {}
            tables = ['master_bot_data', 'client_bot_signups', 'user_session_data']
            
            for table in tables:
                cur.execute(f"SELECT * FROM {table}")
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                
                # Convert datetime objects to strings
                formatted_rows = []
                for row in rows:
                    formatted_row = []
                    for item in row:
                        if isinstance(item, datetime):
                            formatted_row.append(item.isoformat())
                        else:
                            formatted_row.append(str(item) if item is not None else None)
                    formatted_rows.append(formatted_row)
                
                backup_data[table] = {
                    'columns': columns,
                    'rows': formatted_rows
                }
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            conn.close()
            return {"status": "success", "file": backup_file, "message": "Backup created successfully"}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def cleanup_old_backups(self, keep_days=7):
        """Remove backups older than specified days"""
        try:
            import time
            current_time = time.time()
            removed_count = 0
            
            for filename in os.listdir(self.backup_dir):
                if filename.startswith('backup_') and filename.endswith('.json'):
                    file_path = os.path.join(self.backup_dir, filename)
                    file_age = current_time - os.path.getctime(file_path)
                    
                    if file_age > (keep_days * 24 * 3600):
                        os.remove(file_path)
                        removed_count += 1
            
            return {"status": "success", "removed": removed_count}
        except Exception as e:
            return {"status": "error", "message": str(e)}