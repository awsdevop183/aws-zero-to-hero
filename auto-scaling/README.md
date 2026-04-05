# ShopScale — AWS Autoscaling Demo

E-commerce product catalog · Flask + MySQL RDS · Ubuntu 24.04 · Custom AMI + ASG

---

## Architecture

```
Your Browser / Locust EC2
         ↓
  aws365.shop (Route 53 / DNS)
         ↓
  Application Load Balancer (port 80 / 443)
         ↓
  Auto Scaling Group
  ┌─────────────────────────────────────────┐
  │  EC2 Ubuntu 24.04 (from Custom AMI)     │
  │  systemd → Gunicorn → Flask app         │
  │  min: 1 · desired: 1 · max: 5          │
  │  Scale out: CPU > 50%                   │
  └─────────────────────────────────────────┘
         ↓
  RDS MySQL 8.0 (shopscale DB)
```

---

## Project Files

```
shopscale/
├── app.py          # Flask app (UI + REST API)
├── schema.sql      # MySQL schema + 24 seed products
├── locustfile.py   # Locust load test (deploy on separate EC2)
└── user-data.sh    # ASG Launch Template bootstrap script
```

---

## Part 1 — RDS MySQL Setup

### 1.1 Create RDS instance
```
RDS → Create Database
Engine:         MySQL 8.0
Template:       Free tier (demo) / Production (real)
Instance:       db.t3.micro
DB name:        shopscale
Username:       admin
Password:       <your-password>
VPC:            same VPC as your EC2s
Public access:  No
Security group: allow port 3306 from EC2 security group only
```

### 1.2 Seed the database
Run this once from any EC2 in the same VPC:
```bash
sudo apt install mysql-client -y
mysql -h YOUR_RDS_ENDPOINT -u admin -p < schema.sql
```

Verify:
```bash
mysql -h YOUR_RDS_ENDPOINT -u admin -p shopscale -e "SELECT COUNT(*) FROM products;"
# Should return: 24
```

---

## Part 2 — Build the Base EC2 (Ubuntu 24.04)

### 2.1 Launch EC2
```
EC2 → Launch Instance
Name:           shopscale-base
AMI:            Ubuntu Server 24.04 LTS
Instance type:  t3.micro
Key pair:       your-key
Security group: allow 22 (your IP only), 80 (anywhere)
```

### 2.2 Connect and install dependencies
```bash
ssh -i your-key.pem ubuntu@<ec2-public-ip>

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3 python3-pip python3-venv -y

# Create app directory
sudo mkdir /app
sudo chown ubuntu:ubuntu /app
cd /app

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install packages
pip install flask gunicorn mysql-connector-python
```

### 2.3 Deploy app files
```bash
# From your local machine
scp -i your-key.pem app.py ubuntu@<ec2-public-ip>:/app/

# Or create directly on EC2
vi /app/app.py    # paste app.py contents
```

### 2.4 Create env file
```bash
sudo vi /etc/shopscale.env
```

```ini
DB_HOST=asg.c8pqywawgz1b.us-east-1.rds.amazonaws.com
DB_PORT=3306
DB_USER=admin
DB_PASS=India156789
DB_NAME=shopscale
INSTANCE_ID=placeholder
SECRET_KEY=HKsdhksjh87hshd789ihhdshdshd7
```

```bash
# Lock down the file (contains credentials)
sudo chmod 600 /etc/shopscale.env
```

### 2.5 Create systemd service

Ubuntu 24.04 uses IMDSv2 — the token step is required to fetch instance metadata.

```bash
sudo vi /etc/systemd/system/shopscale.service
```

```ini
[Unit]
Description=ShopScale E-commerce App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/app
EnvironmentFile=/etc/shopscale.env
ExecStartPre=+/bin/bash -c '\
  TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 21600"); \
  INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
    http://169.254.169.254/latest/meta-data/instance-id); \
  grep -q "^INSTANCE_ID=" /etc/shopscale.env \
    && sed -i "s/^INSTANCE_ID=.*/INSTANCE_ID=$INSTANCE_ID/" /etc/shopscale.env \
    || echo "INSTANCE_ID=$INSTANCE_ID" >> /etc/shopscale.env'
ExecStart=/app/venv/bin/gunicorn --workers 4 --bind 0.0.0.0:80 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable shopscale
sudo systemctl start shopscale

# Check status
sudo systemctl status shopscale

```
If gunicorn needs to bind to port 80, grant the Python binary permission to use low ports:

```bash
# Step 1: Find the real Python binary (venv uses symlinks)
readlink -f /app/venv/bin/python3

# Step 2: Apply the capability to the real binary path from Step 1
sudo setcap 'cap_net_bind_service=+ep' /usr/bin/python3.12
```

# Restart shopscale service
sudo systemctl restart shopscale

### 2.6 Verify everything works
```bash
# Health check — must show db: connected
curl http://localhost/health

# Products API — must return 24 products
curl http://localhost/api/products | python3 -m json.tool | head -30

# Open in browser
http://<ec2-public-ip>
```

Both must work before proceeding. ✅

---

## Part 3 — Create Custom AMI

### 3.1 Stop the instance (clean snapshot)
```
EC2 → Instances → select shopscale-base → Instance State → Stop
```

### 3.2 Create AMI
```
EC2 → Instances → select shopscale-base
→ Actions → Image and Templates → Create Image

Image name:   shopscale-ubuntu-v1
Description:  ShopScale, Ubuntu 24.04, Python venv, Gunicorn 4 workers
No reboot:    leave unchecked

→ Create Image
```

Wait 5-10 minutes. Go to EC2 → AMIs → note your `ami-xxxxxxxxxxxxxxxxx` ID.

---

## Part 4 — Application Load Balancer

### 4.1 Create Target Group
```
EC2 → Target Groups → Create Target Group
Target type:         Instances
Name:                shopscale-tg
Protocol:            HTTP
Port:                80
Health check path:   /health
Healthy threshold:   2
Unhealthy threshold: 2
Interval:            15 seconds
```

### 4.2 Create ALB
```
EC2 → Load Balancers → Create → Application Load Balancer
Name:           shopscale-alb
Scheme:         Internet-facing
VPC:            your VPC
Subnets:        select at least 2 AZs
Security group: allow 80 and 443
Listener:       HTTP:80 → forward to shopscale-tg
→ Create
```

### 4.3 HTTPS with aws365.shop
```
1. ACM → Request Certificate → aws365.shop → DNS validation
2. ALB → Listeners → Add HTTPS :443 → attach ACM cert
3. HTTP :80 listener → redirect to HTTPS :443
4. DNS:
   Route 53:        A record (Alias) → shopscale-alb-xxx.us-east-1.elb.amazonaws.com
   Other registrar: CNAME → shopscale-alb-xxx.us-east-1.elb.amazonaws.com
```

---

## Part 5 — Launch Template

```
EC2 → Launch Templates → Create Launch Template
Name:           shopscale-lt
AMI:            ami-xxxxxxxxxxxxxxxxx  ← your custom AMI
Instance type:  t3.micro
Key pair:       your-key
Security group: allow 80 from ALB SG only, 22 from your IP only
```

**User Data** (paste in Advanced Details section):
```bash
#!/bin/bash
# App is already installed in the AMI
# Just inject DB credentials and restart the service
# Uses IMDSv2 — required on Ubuntu 24.04

# Step 1: Get IMDSv2 token
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

# Step 2: Fetch instance ID using token
INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/instance-id)

# Step 3: Write env file
cat > /etc/shopscale.env << ENVEOF
DB_HOST=YOUR_RDS_ENDPOINT.us-east-1.rds.amazonaws.com
DB_PORT=3306
DB_USER=admin
DB_PASS=YOUR_DB_PASSWORD
DB_NAME=shopscale
INSTANCE_ID=$INSTANCE_ID
ENVEOF

# Step 4: Secure and restart
chmod 600 /etc/shopscale.env
systemctl restart shopscale

echo "ShopScale started on $INSTANCE_ID"
```

> Replace `DB_HOST` and `DB_PASS` with your actual values before saving.

---

## Part 6 — Auto Scaling Group

```
EC2 → Auto Scaling Groups → Create

Step 1 — Template
Name:             shopscale-asg
Launch template:  shopscale-lt

Step 2 — Network
VPC:     your VPC
Subnets: select 2-3 AZs (us-east-1a, 1b, 1c)

Step 3 — Load balancing
Attach to:         existing ALB target group
Target group:      shopscale-tg
Health check type: ELB
Grace period:      60 seconds

Step 4 — Capacity
Minimum:  1
Desired:  1
Maximum:  5

Step 5 — Scaling policy
Policy type:   Target Tracking
Metric:        Average CPU utilization
Target value:  50%
Warm-up:       60 seconds

→ Create Auto Scaling Group ✅
```

---

## Part 7 — Locust Load Generator

Deploy on a **separate** EC2 — NOT inside the ASG.

### 7.1 Launch Locust EC2
```
AMI:            Ubuntu 24.04 LTS
Instance type:  t3.micro
Security group: allow 22 (your IP), 8089 (your IP only)
```

### 7.2 Install Docker and run Locust
```bash
ssh -i your-key.pem ubuntu@<locust-ec2-ip>

# Install Docker
sudo apt update
sudo apt install docker.io -y
sudo systemctl start docker
sudo usermod -aG docker ubuntu

# Log out and back in, then:
mkdir locust && cd locust

cat > locustfile.py << 'LOCUST'
from locust import HttpUser, task, between
import random

class ShopUser(HttpUser):
    wait_time = between(1, 3)

    @task(5)
    def browse_products(self):
        self.client.get("/api/products")

    @task(3)
    def view_homepage(self):
        self.client.get("/")

    @task(2)
    def search_products(self):
        terms = ["merino", "keyboard", "yoga", "coffee"]
        self.client.get(f"/api/search?q={random.choice(terms)}")

    @task(1)
    def add_to_cart(self):
        self.client.post("/api/cart", json={
            "product_id": random.randint(1, 24),
            "quantity": 1,
            "session_id": f"user-{random.randint(1000, 9999)}"
        })
LOCUST

docker run -d \
  --name locust \
  --restart always \
  -p 8089:8089 \
  -v $(pwd):/mnt/locust \
  locustio/locust \
  -f /mnt/locust/locustfile.py
```

### 7.3 Open Locust UI
```
http://<locust-ec2-ip>:8089
Host: https://aws365.shop
```

---

## Part 8 — Demo Script (Video)

| Step | Locust users | What to show on screen |
|------|-------------|------------------------|
| 1 | 10 | App loading normally, low CPU (~15%) in CloudWatch |
| 2 | 100 | CPU climbing, DB ms rising in app header |
| 3 | 300 | CPU > 50% — CloudWatch alarm fires |
| 4 | — | ASG Activity tab — new instance launching |
| 5 | — | Target group — new instance status: healthy |
| 6 | — | Refresh app — instance ID in navbar changes |
| 7 | Stop | CPU drops — scale-in after ~5 min cooldown |

---

## Part 9 — Updating the App

When `app.py` changes:
```bash
# 1. Launch a new EC2 from your existing AMI
# 2. SSH in, update /app/app.py
# 3. Test: curl http://localhost/health
# 4. Create new AMI: shopscale-ubuntu-v2
# 5. Update Launch Template → point to new AMI
# 6. Instance Refresh:
#    EC2 → ASG → shopscale-asg → Instance Refresh → Start
#    Min healthy percentage: 50%
#    AWS replaces instances one by one — zero downtime
```

---

## Part 10 — Troubleshooting

```bash
# App not starting
sudo systemctl status shopscale
sudo journalctl -u shopscale -n 50

# Tail live logs
sudo journalctl -u shopscale -f

# Check env vars loaded correctly
sudo cat /etc/shopscale.env

# Verify IMDSv2 works manually
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/instance-id

# Test DB connection
source /app/venv/bin/activate
python3 -c "
import mysql.connector
db = mysql.connector.connect(
  host='YOUR_RDS_ENDPOINT',
  user='admin', password='yourpassword', database='shopscale'
)
print('Connected!')
"

# Check Gunicorn is listening on port 80
sudo ss -tlnp | grep :80

# Check ALB health check
curl -v http://localhost/health
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Product catalog UI |
| GET | `/health` | ALB health check → `{"status":"healthy","db":"connected"}` |
| GET | `/api/products` | All products (JOIN query) |
| GET | `/api/products/:id` | Single product detail |
| GET | `/api/search?q=` | Search by name or description |
| POST | `/api/cart` | Add to cart (DB write) |
