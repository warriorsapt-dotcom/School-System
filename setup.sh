#!/bin/bash
# Quick Setup Script for School Platform

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}School Platform - Quick Setup${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Check Python installation
echo -e "${YELLOW}[1/7] Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found: $(python3 --version)${NC}\n"

# Check PostgreSQL installation
echo -e "${YELLOW}[2/7] Checking PostgreSQL installation...${NC}"
if ! command -v psql &> /dev/null; then
    echo -e "${RED}PostgreSQL is not installed. Please install PostgreSQL 12 or higher.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL found: $(psql --version)${NC}\n"

# Create virtual environment
echo -e "${YELLOW}[3/7] Creating virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Skipping...${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}\n"

# Install dependencies
echo -e "${YELLOW}[4/7] Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}\n"

# Create .env file
echo -e "${YELLOW}[5/7] Setting up environment variables...${NC}"
if [ -f ".env" ]; then
    echo -e "${YELLOW}.env file already exists. Skipping...${NC}"
else
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created from template${NC}"
    echo -e "${YELLOW}Please edit .env with your configuration${NC}"
fi
echo ""

# Create logs directory
echo -e "${YELLOW}[6/7] Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p media/profile_pictures
mkdir -p media/school_images
mkdir -p staticfiles
echo -e "${GREEN}✓ Directories created${NC}\n"

# Run migrations
echo -e "${YELLOW}[7/7] Running database migrations...${NC}"
python manage.py migrate
echo -e "${GREEN}✓ Migrations applied${NC}\n"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit .env file with your database credentials and other settings"
echo "2. Create a superuser: python manage.py createsuperuser"
echo "3. Load initial data: python manage.py shell < initial_data.py"
echo "4. Start development server: python manage.py runserver"
echo ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo "- python manage.py createsuperuser          # Create admin user"
echo "- python manage.py runserver                # Start dev server"
echo "- python manage.py makemigrations          # Create migrations"
echo "- python manage.py migrate                 # Apply migrations"
echo "- python manage.py test                    # Run tests"
echo ""
echo -e "${GREEN}Documentation: See SETUP_GUIDE.md${NC}"
