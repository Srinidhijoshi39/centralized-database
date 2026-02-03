# Centralized Trading Database

A Flask-based web application for managing and viewing trading bot data with PostgreSQL database integration. This system provides a centralized dashboard for monitoring trading activities, client data, and session management.

## 🚀 Features

- **📊 Database Viewer**: Interactive web interface to view trading data across multiple tables
- **💾 Backup Management**: Automated database backup system with JSON export
- **🔄 Connection Pooling**: Efficient PostgreSQL connection management with failover
- **📱 Responsive UI**: Clean, mobile-friendly web interface for data visualization
- **🔒 Security**: Input validation, SQL injection protection, and secure session management
- **📈 Real-time Data**: Live session tracking and trading statistics
- **🔍 Session Details**: Detailed view of individual trading sessions with PnL tracking

## 📋 Tables Managed

- **`master_bot_data`**: Bot configuration and client information
- **`client_bot_signups`**: Client registration and authentication data
- **`user_session_data`**: Daily trading session records with detailed metrics

## 🛠️ Quick Setup

### Prerequisites
- Python 3.7+
- PostgreSQL 12+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Srinidhijoshi39/centralized-trading-database.git
   cd centralized-trading-database
   ```

2. **Run setup script**
   ```bash
   python setup.py
   ```

3. **Configure environment**
   ```bash
   # Edit .env file with your database credentials
   notepad .env  # Windows
   nano .env     # Linux/macOS
   ```

4. **Start the application**
   ```bash
   # Activate virtual environment first
   # Windows:
   venv\Scripts\activate
   # Linux/macOS:
   source venv/bin/activate
   
   python app.py
   ```

5. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database Configuration
DB_HOST=localhost
DB_NAME=trading_master_db
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_PORT=5432

# Application Configuration
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here-change-in-production

# Backup Configuration
BACKUP_DIR=./backups
```

### Database Schema

The application expects the following PostgreSQL tables:

```sql
-- Master bot data table
CREATE TABLE master_bot_data (
    sl_number SERIAL PRIMARY KEY,
    client_id VARCHAR(50),
    bot_id VARCHAR(50),
    name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Client signups table
CREATE TABLE client_bot_signups (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50),
    username VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    aadhar VARCHAR(20),
    qr_key TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User session data table
CREATE TABLE user_session_data (
    id SERIAL PRIMARY KEY,
    client_id VARCHAR(50),
    session_date DATE,
    login_time TIMESTAMP,
    logout_time TIMESTAMP,
    kite_id VARCHAR(50),
    username VARCHAR(100),
    kite_username VARCHAR(100),
    mode VARCHAR(20),
    total_trades INTEGER DEFAULT 0,
    net_pnl DECIMAL(10,2) DEFAULT 0.00,
    gross_pnl DECIMAL(10,2) DEFAULT 0.00,
    charges DECIMAL(10,2) DEFAULT 0.00
);
```

## 🔌 API Endpoints

### Web Interface
- `GET /` - Main database viewer interface
- `GET /view_data?db=<table_name>` - View specific table data
- `GET /session_details/<client_id>/<date>` - Detailed session view

### REST API
- `GET /api/get-latest-data/<table_name>` - Get latest data via API
- `POST /api/sync-signup` - Sync client signup data
- `POST /api/sync-session` - Sync trading session data
- `POST /api/backup-database` - Create database backup
- `GET /api/session_details_json/<client_id>/<date>` - Session details as JSON

### Debug Endpoints
- `GET /api/debug-data/<client_id>` - Debug client data
- `POST /api/test-pc3-payload` - Test payload reception
- `GET /test-session/<client_id>` - Test session data

## 🔧 Development

### Running in Development Mode

```bash
# Set debug mode in .env
FLASK_DEBUG=True

# Run with auto-reload
python app.py
```

### Backup Scheduler

Run the backup scheduler for automated daily backups:

```bash
python backup_scheduler.py
```

## 📦 Dependencies

- **Flask 2.3.3**: Web framework
- **Flask-CORS 4.0.0**: Cross-origin resource sharing
- **psycopg2-binary 2.9.7**: PostgreSQL adapter
- **python-dotenv 1.0.0**: Environment variable management
- **schedule 1.2.0**: Task scheduling
- **requests 2.31.0**: HTTP library

## 🚀 Deployment

### Production Deployment

1. **Use a production WSGI server**:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **Set up reverse proxy** (Nginx example):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Environment Configuration**:
   - Set `FLASK_DEBUG=False`
   - Use strong `SECRET_KEY`
   - Configure proper database credentials
   - Set up SSL/TLS certificates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Srinidhi Joshi**
- GitHub: [@Srinidhijoshi39](https://github.com/Srinidhijoshi39)

## 🙏 Acknowledgments

- Flask community for the excellent web framework
- PostgreSQL team for the robust database system
- All contributors who help improve this project