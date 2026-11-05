# Deploying Meikipop OCR to AWS EC2

This guide walks you through deploying the **Meikipop OCR Web & WebSocket Server** onto an Amazon Web Services (AWS) EC2 instance, accessible over the internet with an interactive web UI, API, and secure HTTPS/WSS.

---

## Architecture Overview

```
                      ┌──────────────────────────────────────────────┐
                      │                 AWS EC2                      │
                      │                                              │
                      │   ┌──────────────────────────────────────┐   │
                      │   │       Nginx (Port 80 / 443)          │   │
                      │   │  • SSL Termination (Let's Encrypt)   │   │
User Browser / API ───┼──►│  • WebSocket Upgrade (HTTP 101)      │   │
                      │   │  • Max upload size: 50MB             │   │
                      │   └──────────────────┬───────────────────┘   │
                      │                      │ http://127.0.0.1:8080 │
                      │   ┌──────────────────▼───────────────────┐   │
                      │   │        Meikipop OCR Server           │   │
                      │   │  • Web UI (GET /)                    │   │
                      │   │  • REST API (POST /ocr)              │   │
                      │   │  • WebSocket (GET /ws)               │   │
                      │   │  • Provider: glensv2                 │   │
                      │   └──────────────────────────────────────┘   │
                      └──────────────────────────────────────────────┘
```

---

## Phase 1: Launch Your EC2 Instance

### 1. Log in to AWS Management Console
Navigate to **EC2** → **Instances** → Click **Launch instances**.

### 2. Configure Instance Settings
* **Name**: `meikipop-ocr-server`
* **Application and OS Images (AMI)**: `Ubuntu Server 24.04 LTS (HVM), SSD Volume Type` (64-bit x86 or ARM)
* **Instance Type**:
  * **Recommended**: `t3.small` (2 vCPU, 2 GiB RAM, ~$15/month)
  * **Free Tier Option**: `t3.micro` or `t2.micro` (1 vCPU, 1 GiB RAM). *Note: if using micro, create a 2GB swap file to prevent out-of-memory during dependency installation.*
* **Key pair (login)**:
  * Select an existing key pair or click **Create new key pair** (e.g. `meikipop-key.pem`).
  * Download and keep this file safe on your computer.

### 3. Configure Network & Security Group
Under **Network settings**:
* Ensure **Auto-assign public IP** is **Enable**
* Check:
  * `[x]` **Allow SSH traffic from**: `My IP` (for security) or `Anywhere (0.0.0.0/0)`
  * `[x]` **Allow HTTP traffic from the internet** (Port 80)
  * `[x]` **Allow HTTPS traffic from the internet** (Port 443)

### 4. Configure Storage
* 20 GiB **gp3** SSD (default 8 GiB can fill up quickly with Docker and package caches).

Click **Launch instance**.

---

## Phase 2: Assign an Elastic IP (Recommended)

By default, an EC2 instance changes its public IP address every time it stops or restarts. An Elastic IP provides a static, permanent public IP address.

1. Go to **EC2 Console** → **Network & Security** → **Elastic IPs**.
2. Click **Allocate Elastic IP address** → **Allocate**.
3. Select your new IP → **Actions** → **Associate Elastic IP address**.
4. Choose your `meikipop-ocr-server` instance and click **Associate**.

---

## Phase 3: Connect and Prepare the Server

### 1. SSH into your EC2 Instance
From your local terminal (where you saved your `.pem` key):

```bash
chmod 400 /path/to/meikipop-key.pem
ssh -i /path/to/meikipop-key.pem ubuntu@<YOUR_EC2_PUBLIC_IP>
```

### 2. Update System Packages
```bash
sudo apt update && sudo apt upgrade -y
```

### 3. (If on t3.micro/1GB RAM) Create a Swap File
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

---

## Phase 4: Deploy the Server

You can deploy using either **Option A (Docker - Recommended)** or **Option B (Direct Systemd)**.

### Option A: Deploy with Docker Compose (Recommended)

#### 1. Install Docker & Docker Compose on EC2
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Apply group changes
newgrp docker
```

#### 2. Copy the Project to EC2
On your local machine, run `rsync` or `scp` to upload the folder:

```bash
rsync -avz --exclude='venv' --exclude='__pycache__' -e "ssh -i /path/to/meikipop-key.pem" \
  /home/ba/meikipop-ocr-server/ ubuntu@<YOUR_EC2_PUBLIC_IP>:~/meikipop-ocr-server/
```

#### 3. Start the Application
On your EC2 instance:

```bash
cd ~/meikipop-ocr-server

# Build and start both OCR server and Nginx in background
docker compose up -d --build
```

#### 4. Verify Containers
```bash
docker compose ps
docker compose logs -f ocr-server
```

You can now open `http://<YOUR_EC2_PUBLIC_IP>` in your browser!

---

### Option B: Deploy Directly with Python & Systemd

If you prefer running directly without Docker:

#### 1. Install Python & Build Tools
```bash
sudo apt install -y python3-pip python3-venv nginx
```

#### 2. Copy the Project to EC2
On your local machine:
```bash
rsync -avz --exclude='venv' --exclude='__pycache__' -e "ssh -i /path/to/meikipop-key.pem" \
  /home/ba/meikipop-ocr-server/ ubuntu@<YOUR_EC2_PUBLIC_IP>:~/meikipop-ocr-server/
```

#### 3. Setup Virtual Environment on EC2
```bash
cd ~/meikipop-ocr-server
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install .
```

#### 4. Configure Systemd Service
```bash
sudo cp meikipop-ocr.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now meikipop-ocr
sudo systemctl status meikipop-ocr
```

#### 5. Configure Nginx
```bash
sudo cp nginx.conf /etc/nginx/sites-available/meikipop
sudo ln -sf /etc/nginx/sites-available/meikipop /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx
```

---

## Phase 5: Domain & Free SSL (Let's Encrypt)

> [!IMPORTANT]
> Modern web browsers restrict clipboard pasting (`Ctrl+V`) and microphone/camera APIs unless your site is served over **HTTPS** (or `localhost`). Additionally, secure WebSocket connections require `wss://`.

### 1. Point Your Domain to Your EC2 Elastic IP
Add an **A Record** in your DNS provider (Cloudflare, Route53, Namecheap, etc.):
* **Type**: `A`
* **Name**: `ocr` (or `@`)
* **Value**: `<YOUR_EC2_PUBLIC_IP>`

### 2. Install Certbot
On your EC2 instance:

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 3. Generate Free Certificate
```bash
sudo certbot --nginx -d yourdomain.com
```
Follow the interactive prompts. Certbot will automatically adjust your Nginx configuration to enable HTTPS and renew certificates automatically.

---

## Phase 6: Testing & Health Check

### Test via Web Browser
Visit `https://yourdomain.com` (or `http://<YOUR_EC2_PUBLIC_IP>`):
- Drag and drop an image or paste with `Ctrl+V`
- Hover over the recognized text to highlight bounding boxes on the image
- Switch between **HTTP** and **WebSocket** modes

### Test via cURL
```bash
# Health check
curl http://<YOUR_EC2_PUBLIC_IP>/health

# Image OCR
curl -X POST http://<YOUR_EC2_PUBLIC_IP>/ocr \
  --data-binary @test_image.png \
  -H "Content-Type: application/octet-stream"
```

---

## Maintenance & Commands Cheat Sheet

| Task | Command |
|---|---|
| View OCR server logs | `docker compose logs -f ocr-server` (or `sudo journalctl -u meikipop-ocr -f`) |
| Restart server | `docker compose restart` (or `sudo systemctl restart meikipop-ocr`) |
| Update code | `git pull && docker compose up -d --build` |
| View active ports | `sudo ss -tulpn` |
| Check memory & CPU | `htop` or `docker stats` |
