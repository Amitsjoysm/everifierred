# MailGuard - Production Deployment Guide

## 🚀 Quick Start

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Domain name with SSL certificate
- Razorpay account with live keys

### Step 1: Configure Environment Variables

#### Backend Configuration

```bash
# Copy example and edit
cp backend/.env.production.example backend/.env

# Edit backend/.env with your values:
nano backend/.env
```

**Required Variables:**
```env
# MongoDB
MONGO_URL=mongodb://mongodb:27017
DB_NAME=email_verifier_db

# Redis
REDIS_URL=redis://redis:6379/0

# JWT - CHANGE THIS!
SECRET_KEY=your-super-secret-random-key-min-32-chars

# Email SMTP
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password

# Razorpay LIVE Keys
RAZORPAY_KEY_ID=rzp_live_YOUR_ACTUAL_KEY
RAZORPAY_KEY_SECRET=YOUR_ACTUAL_SECRET
RAZORPAY_WEBHOOK_SECRET=YOUR_WEBHOOK_SECRET

# CORS - Your domain
CORS_ORIGINS=https://yourdomain.com

# App URL
APP_URL=https://yourdomain.com
```

#### Frontend Configuration

```bash
# Copy example and edit
cp frontend/.env.production.example frontend/.env.production

# Edit frontend/.env.production:
nano frontend/.env.production
```

**Required Variables:**
```env
REACT_APP_BACKEND_URL=https://api.yourdomain.com
```

---

### Step 2: Build and Deploy

#### Option 1: Using Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Option 2: Using Makefile

```bash
# Deploy to production
make deploy

# Check status
make status

# View logs
make logs
```

---

### Step 3: Initial Setup

#### Create Super Admin Account

```bash
# Access backend container
docker exec -it mailguard-backend bash

# Create admin
python create_custom_admin.py "admin@yourdomain.com" "SecurePassword123!"

# Exit container
exit
```

#### Seed Database (Optional)

```bash
# Seed with default plans, blogs, FAQs
docker exec -it mailguard-backend python seed_data.py
```

---

### Step 4: Configure Reverse Proxy (Nginx/Caddy)

#### Option A: Nginx

```nginx
# /etc/nginx/sites-available/mailguard

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:80;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static HTML pages
    location /html {
        proxy_pass http://localhost:8001;
    }
}
```

#### Option B: Caddy (Simpler)

```caddyfile
yourdomain.com {
    reverse_proxy /api/* localhost:8001
    reverse_proxy /html/* localhost:8001
    reverse_proxy localhost:80
}
```

---

### Step 5: Configure Razorpay Webhooks

1. Go to Razorpay Dashboard → Settings → Webhooks
2. Add webhook URL: `https://yourdomain.com/api/payments/webhook`
3. Select events:
   - payment.captured
   - payment.failed
   - subscription.activated
   - subscription.charged
   - subscription.cancelled
4. Copy webhook secret
5. Add to `backend/.env`: `RAZORPAY_WEBHOOK_SECRET=whsec_xxxxx`
6. Restart backend: `docker-compose restart backend`

---

## 🔧 Service Management

### Start/Stop Services

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart backend
docker-compose restart frontend

# View service status
docker-compose ps
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f celery-worker

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Scale Workers

```bash
# Scale Celery workers to 8
docker-compose up -d --scale celery-worker=8
```

---

## 🗄️ Database Management

### Backup Database

```bash
# Create backup
docker exec mailguard-mongodb mongodump --out=/data/backup/$(date +%Y%m%d)

# Copy backup to host
docker cp mailguard-mongodb:/data/backup ./backups
```

### Restore Database

```bash
# Copy backup to container
docker cp ./backups/20250101 mailguard-mongodb:/data/restore

# Restore
docker exec mailguard-mongodb mongorestore /data/restore/20250101
```

### Access MongoDB Shell

```bash
docker exec -it mailguard-mongodb mongosh email_verifier_db
```

---

## 📊 Monitoring

### Health Checks

```bash
# Check all services health
docker-compose ps

# Check backend health
curl http://localhost:8001/api/health

# Check frontend health
curl http://localhost:80/health
```

### Resource Usage

```bash
# View container stats
docker stats

# Specific container
docker stats mailguard-backend
```

---

## 🔐 Security Checklist

### Before Production:

- [ ] Change `SECRET_KEY` to a strong random string (32+ characters)
- [ ] Use real Razorpay LIVE keys (not test keys)
- [ ] Configure SMTP with your email credentials
- [ ] Set `CORS_ORIGINS` to your actual domain (not *)
- [ ] Enable SSL/HTTPS with valid certificate
- [ ] Configure firewall (allow only 80, 443)
- [ ] Set up database backups (daily)
- [ ] Configure webhook secret
- [ ] Review and update security headers
- [ ] Set up monitoring and alerts
- [ ] Enable Docker secrets for sensitive data

---

## 🚨 Troubleshooting

### Services Not Starting

```bash
# Check logs
docker-compose logs backend

# Check if ports are already in use
sudo lsof -i :8001
sudo lsof -i :80

# Rebuild containers
docker-compose down
docker-compose up -d --build
```

### Database Connection Issues

```bash
# Check MongoDB logs
docker-compose logs mongodb

# Test connection
docker exec mailguard-backend python -c "from database import get_db; import asyncio; asyncio.run(get_db())"
```

### Celery Workers Not Processing

```bash
# Check worker logs
docker-compose logs celery-worker

# Check Redis connection
docker exec mailguard-redis redis-cli ping

# Restart workers
docker-compose restart celery-worker celery-beat
```

---

## 📈 Performance Optimization

### Recommended Production Settings:

```yaml
# docker-compose.override.yml (create this)
version: '3.8'

services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  celery-worker:
    deploy:
      replicas: 4
      resources:
        limits:
          cpus: '1'
          memory: 1G
```

---

## 🔄 Update and Maintenance

### Update Application

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose up -d --build

# Or use zero-downtime update
docker-compose up -d --no-deps --build backend
```

### Database Migration

```bash
# Access backend container
docker exec -it mailguard-backend bash

# Run migration script (if any)
python migrate.py
```

---

## 📊 Monitoring Setup (Optional)

### Add Prometheus + Grafana

```yaml
# Add to docker-compose.yml
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

## 🌐 DNS Configuration

### Point your domain to server:

```
A Record:
yourdomain.com → YOUR_SERVER_IP

A Record:
api.yourdomain.com → YOUR_SERVER_IP

CNAME:
www.yourdomain.com → yourdomain.com
```

---

## 📝 Post-Deployment Checklist

- [ ] All services running (`docker-compose ps`)
- [ ] Backend health check passing
- [ ] Frontend accessible
- [ ] Can login to admin panel
- [ ] Can create users
- [ ] Can create plans with Razorpay IDs
- [ ] Email verification working
- [ ] Payment flow working
- [ ] Invoices generating
- [ ] Subscriptions creating
- [ ] Webhooks receiving events
- [ ] Backups configured
- [ ] Monitoring enabled
- [ ] SSL certificate valid
- [ ] Domain resolving correctly

---

## 🆘 Support

For deployment issues:
- Check logs: `docker-compose logs -f`
- Review health checks: `docker-compose ps`
- Verify environment variables
- Check firewall settings
- Review documentation in `/app/*.md` files

---

**Deployment prepared by:** MailGuard Development Team
**Last updated:** December 2025
**Status:** ✅ Production Ready