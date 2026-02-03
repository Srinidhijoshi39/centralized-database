# Deployment Guide

This guide covers deploying the Centralized Trading Database application to production environments.

## 🚀 Production Deployment Options

### Option 1: Traditional Server Deployment

#### Prerequisites
- Ubuntu 20.04+ or CentOS 8+
- Python 3.8+
- PostgreSQL 13+
- Nginx (recommended)
- SSL certificate

#### Step 1: Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install python3 python3-pip python3-venv nginx postgresql postgresql-contrib

# Create application user
sudo useradd -m -s /bin/bash tradingapp
sudo usermod -aG sudo tradingapp
```

#### Step 2: Database Setup
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE trading_master_db;
CREATE USER tradingapp WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE trading_master_db TO tradingapp;
\q
```

#### Step 3: Application Deployment
```bash
# Switch to application user
sudo su - tradingapp

# Clone repository
git clone https://github.com/Srinidhijoshi39/centralized-trading-database.git
cd centralized-trading-database

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn

# Create production environment file
cp .env.example .env
nano .env  # Edit with production values
```

#### Step 4: Production Environment Configuration
```env
# Production .env file
DB_HOST=localhost
DB_NAME=trading_master_db
DB_USER=tradingapp
DB_PASSWORD=secure_password_here
DB_PORT=5432
FLASK_DEBUG=False
SECRET_KEY=your-very-secure-secret-key-here
BACKUP_DIR=/home/tradingapp/backups
```

#### Step 5: Systemd Service
```bash
# Create systemd service file
sudo nano /etc/systemd/system/tradingapp.service
```

```ini
[Unit]
Description=Trading Database Application
After=network.target

[Service]
User=tradingapp
Group=tradingapp
WorkingDirectory=/home/tradingapp/centralized-trading-database
Environment=PATH=/home/tradingapp/centralized-trading-database/venv/bin
ExecStart=/home/tradingapp/centralized-trading-database/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable tradingapp
sudo systemctl start tradingapp
sudo systemctl status tradingapp
```

#### Step 6: Nginx Configuration
```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/tradingapp
```

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /home/tradingapp/centralized-trading-database/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/tradingapp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 7: SSL Certificate (Let's Encrypt)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Option 2: Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "app:app"]
```

#### Docker Compose
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DB_HOST=db
      - DB_NAME=trading_master_db
      - DB_USER=postgres
      - DB_PASSWORD=secure_password
      - SECRET_KEY=your-secret-key
    depends_on:
      - db
    volumes:
      - ./backups:/app/backups

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=trading_master_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app

volumes:
  postgres_data:
```

### Option 3: Cloud Deployment (AWS)

#### Using AWS Elastic Beanstalk
```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init

# Create environment
eb create production

# Deploy
eb deploy
```

#### Using AWS ECS with Fargate
1. Build and push Docker image to ECR
2. Create ECS cluster
3. Define task definition
4. Create service
5. Configure load balancer

## 🔧 Production Configuration

### Security Checklist
- [ ] Use strong, unique SECRET_KEY
- [ ] Set FLASK_DEBUG=False
- [ ] Use HTTPS in production
- [ ] Configure firewall (UFW/iptables)
- [ ] Regular security updates
- [ ] Database connection encryption
- [ ] Input validation and sanitization
- [ ] Rate limiting (consider using nginx rate limiting)

### Performance Optimization
- [ ] Use connection pooling
- [ ] Configure proper worker count for Gunicorn
- [ ] Set up database indexing
- [ ] Enable Nginx gzip compression
- [ ] Configure static file caching
- [ ] Monitor application performance

### Monitoring and Logging
```bash
# Set up log rotation
sudo nano /etc/logrotate.d/tradingapp
```

```
/home/tradingapp/centralized-trading-database/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 tradingapp tradingapp
}
```

### Backup Strategy
```bash
# Create backup script
nano /home/tradingapp/backup_script.sh
```

```bash
#!/bin/bash
# Database backup script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/tradingapp/backups"
DB_NAME="trading_master_db"

# Create database dump
pg_dump -h localhost -U tradingapp $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Remove backups older than 30 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
```

```bash
# Make executable and add to crontab
chmod +x /home/tradingapp/backup_script.sh
crontab -e

# Add daily backup at 2 AM
0 2 * * * /home/tradingapp/backup_script.sh
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Check database connectivity
   psql -h localhost -U tradingapp -d trading_master_db
   ```

2. **Application Not Starting**
   ```bash
   # Check service logs
   sudo journalctl -u tradingapp -f
   
   # Check application logs
   tail -f /home/tradingapp/centralized-trading-database/logs/app.log
   ```

3. **Nginx Issues**
   ```bash
   # Check Nginx configuration
   sudo nginx -t
   
   # Check Nginx logs
   sudo tail -f /var/log/nginx/error.log
   ```

### Health Checks
```bash
# Application health check
curl -f http://localhost:5000/ || echo "Application is down"

# Database health check
pg_isready -h localhost -U tradingapp
```

## 📊 Monitoring

### Basic Monitoring Script
```bash
#!/bin/bash
# Simple monitoring script

# Check if application is running
if ! curl -f http://localhost:5000/ > /dev/null 2>&1; then
    echo "Application is down - restarting..."
    sudo systemctl restart tradingapp
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Warning: Disk usage is at ${DISK_USAGE}%"
fi

# Check memory usage
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ $MEMORY_USAGE -gt 80 ]; then
    echo "Warning: Memory usage is at ${MEMORY_USAGE}%"
fi
```

This deployment guide provides comprehensive instructions for deploying the application in various production environments. Choose the option that best fits your infrastructure and requirements.