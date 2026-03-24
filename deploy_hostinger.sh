#!/bin/bash

# Hostinger Deployment Script for CRM Portal
# This script automates the deployment process on Hostinger VPS

set -e  # Exit on error

echo "=========================================="
echo "CRM Portal - Hostinger Deployment Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}Please do not run this script as root. Use a regular user with sudo privileges.${NC}"
    exit 1
fi

# Variables
PROJECT_DIR=$(pwd)
VENV_DIR="$PROJECT_DIR/venv"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')

echo -e "${GREEN}Starting deployment...${NC}"
echo "Project Directory: $PROJECT_DIR"
echo "Python Version: $PYTHON_VERSION"
echo ""

# Step 1: Update system packages
echo -e "${YELLOW}[1/10] Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y

# Step 2: Install required packages
echo -e "${YELLOW}[2/10] Installing required packages...${NC}"
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib git curl

# Step 3: Create virtual environment
echo -e "${YELLOW}[3/10] Creating Python virtual environment...${NC}"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv venv
    echo -e "${GREEN}Virtual environment created.${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists.${NC}"
fi

# Step 4: Activate virtual environment and install dependencies
echo -e "${YELLOW}[4/10] Installing Python dependencies...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}Dependencies installed.${NC}"

# Step 5: Check for .env file
echo -e "${YELLOW}[5/10] Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}ERROR: .env file not found!${NC}"
    echo "Please create a .env file with all required environment variables."
    echo "See HOSTINGER_DEPLOYMENT.md for details."
    exit 1
else
    echo -e "${GREEN}.env file found.${NC}"
fi

# Step 6: Run database migrations
echo -e "${YELLOW}[6/10] Running database migrations...${NC}"
python manage.py migrate --noinput
echo -e "${GREEN}Migrations completed.${NC}"

# Step 7: Collect static files
echo -e "${YELLOW}[7/10] Collecting static files...${NC}"
python manage.py collectstatic --noinput
echo -e "${GREEN}Static files collected.${NC}"

# Step 8: Check if superuser exists
echo -e "${YELLOW}[8/10] Checking for superuser...${NC}"
if python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print('SUPERUSER_EXISTS' if User.objects.filter(is_superuser=True).exists() else 'NO_SUPERUSER')" | grep -q "SUPERUSER_EXISTS"; then
    echo -e "${GREEN}Superuser already exists.${NC}"
else
    echo -e "${YELLOW}No superuser found. Please create one:${NC}"
    python manage.py createsuperuser
fi

# Step 9: Create systemd service file
echo -e "${YELLOW}[9/10] Setting up systemd service...${NC}"
SERVICE_FILE="/etc/systemd/system/crm-portal.service"
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=CRM Portal Gunicorn daemon
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn \\
    --config $PROJECT_DIR/gunicorn_config.py \\
    college_management_system.wsgi:application

Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable crm-portal
echo -e "${GREEN}Systemd service configured.${NC}"

# Step 10: Start services
echo -e "${YELLOW}[10/10] Starting services...${NC}"
sudo systemctl restart crm-portal
sudo systemctl restart nginx

# Check service status
if sudo systemctl is-active --quiet crm-portal; then
    echo -e "${GREEN}✓ Gunicorn service is running${NC}"
else
    echo -e "${RED}✗ Gunicorn service failed to start${NC}"
    echo "Check logs with: sudo journalctl -u crm-portal -n 50"
fi

if sudo systemctl is-active --quiet nginx; then
    echo -e "${GREEN}✓ Nginx service is running${NC}"
else
    echo -e "${RED}✗ Nginx service failed to start${NC}"
    echo "Check logs with: sudo tail -f /var/log/nginx/error.log"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Deployment completed!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Configure Nginx (see HOSTINGER_DEPLOYMENT.md)"
echo "2. Setup SSL certificate: sudo certbot --nginx -d yourdomain.com"
echo "3. Point your domain to this server's IP"
echo ""
echo "Useful commands:"
echo "  - Check status: sudo systemctl status crm-portal"
echo "  - View logs: sudo journalctl -u crm-portal -f"
echo "  - Restart: sudo systemctl restart crm-portal"
echo ""
