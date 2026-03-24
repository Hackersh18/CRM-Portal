# Quick Deployment Guide - Hostinger VPS

## 🚀 Fast Track Deployment (30 minutes)

### Prerequisites
- Hostinger VPS access (SSH)
- Domain name pointed to VPS IP
- Git repository access

### Quick Steps

#### 1. Connect to VPS
```bash
ssh root@your-vps-ip
```

#### 2. Run Automated Script
```bash
# Clone repository
git clone https://github.com/yourusername/CRM-Portal-main.git
cd CRM-Portal-main

# Make script executable
chmod +x deploy_hostinger.sh

# Run deployment script
./deploy_hostinger.sh
```

#### 3. Manual Steps (After Script)

**A. Create .env file:**
```bash
nano .env
```
Add all required environment variables (see HOSTINGER_DEPLOYMENT.md)

**B. Setup Database:**
```bash
sudo -u postgres psql
```
```sql
CREATE DATABASE crm_db;
CREATE USER crm_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE crm_db TO crm_user;
\q
```

**C. Configure Nginx:**
```bash
# Copy nginx config
sudo cp nginx_config.conf /etc/nginx/sites-available/crm-portal

# Edit and update domain name
sudo nano /etc/nginx/sites-available/crm-portal

# Enable site
sudo ln -s /etc/nginx/sites-available/crm-portal /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**D. Setup SSL:**
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

#### 4. Verify Deployment
```bash
# Check services
sudo systemctl status crm-portal
sudo systemctl status nginx

# Test application
curl http://localhost:8000
```

---

## 💰 Cost Summary

| Item | Cost | Frequency |
|------|------|-----------|
| VPS 2 (2GB RAM) | $4.99 | Monthly |
| Domain | $0.99-$15 | Yearly |
| SSL Certificate | FREE | Included |
| **Total** | **$4.99/month** | + Domain |

---

## 📋 Environment Variables Template

Create `.env` file with:

```env
SECRET_KEY=generate-with-python-secrets-token-urlsafe
DJANGO_DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://crm_user:password@localhost:5432/crm_db
TIME_ZONE=Asia/Kolkata
USE_TZ=True
```

Generate SECRET_KEY:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 🔧 Common Commands

```bash
# Restart application
sudo systemctl restart crm-portal

# View logs
sudo journalctl -u crm-portal -f

# Run migrations
cd /path/to/project
source venv/bin/activate
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser
```

---

For detailed instructions, see **HOSTINGER_DEPLOYMENT.md**
