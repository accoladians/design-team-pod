# Design Team Pod Deployment Guide

Complete production deployment guide for the containerized pixel-perfect design toolkit.

## Quick Start

```bash
# Navigate to design team pod directory
cd /srv/xwander-platform/tools/design-team-pod

# Test the deployment
./test-deployment.sh

# Deploy to production
export ANTHROPIC_API_KEY="your_key_here"
export OPENAI_API_KEY="your_key_here"
./deploy.sh

# Check status
systemctl --user status design-team-pod.service
curl http://127.0.0.1:8081/health
```

## Prerequisites

### System Requirements
- **OS**: Linux with systemd (Ubuntu 20.04+ recommended)
- **Podman**: Version 3.4+ (for Quadlet support)
- **Disk Space**: 10GB minimum, 50GB recommended
- **Memory**: 4GB minimum, 8GB recommended
- **CPU**: 2+ cores recommended

### Software Dependencies
```bash
# Install Podman (Ubuntu/Debian)
sudo apt update
sudo apt install podman

# Enable user systemd services
sudo loginctl enable-linger $USER

# Install additional tools
sudo apt install jq bc curl git
```

### API Keys (Optional but Recommended)
```bash
# Required for AI analysis features
export ANTHROPIC_API_KEY="your_anthropic_key"
export OPENAI_API_KEY="your_openai_key"
export GOOGLE_API_KEY="your_google_key"  # Future feature
```

## Deployment Process

### Step 1: Pre-Deployment Testing
```bash
# Run comprehensive test suite
./test-deployment.sh

# This will:
# - Build the container image
# - Test all functionality
# - Validate security features
# - Check performance metrics
# - Generate test report
```

### Step 2: Production Deployment
```bash
# Deploy with security-first configuration
./deploy.sh

# Monitor deployment
journalctl --user -u design-team-pod.service -f
```

### Step 3: Verification
```bash
# Check service status
systemctl --user status design-team-pod.service

# Test API endpoints
curl http://127.0.0.1:8081/health
curl http://127.0.0.1:8081/

# Access documentation
open http://127.0.0.1:8081/docs
```

## Configuration

### Environment Variables
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8080
LOG_LEVEL=info

# Workspace Configuration
WORKSPACE_DIR=/app/workspace
TOOLS_DIR=/app/tools
KNOWLEDGE_DIR=/app/knowledge

# AI Provider Keys
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
GOOGLE_API_KEY=your_key
```

### Volume Mounts
```bash
# Data persistence locations
/data/design-team/workspace/    # Project data and analysis results
/data/design-team/knowledge/    # Documentation and lessons learned
/data/design-team/config/       # Configuration files
```

### Network Configuration
```bash
# Default binding (localhost only for security)
127.0.0.1:8081 -> container:8080

# For external access (configure firewall appropriately)
# Edit design-team.container:
# PublishPort=0.0.0.0:8081:8080
```

## Security Features

### Container Security
- **Rootless Operation**: Runs as UID 1000, never root
- **Read-Only Filesystem**: Immutable container filesystem
- **Dropped Capabilities**: All capabilities dropped except NET_BIND_SERVICE
- **No New Privileges**: Prevents privilege escalation
- **SELinux Labels**: Full SELinux integration

### Network Security
- **Localhost Binding**: API only accessible from localhost by default
- **Isolated Network**: Container runs in isolated bridge network
- **No Host Networking**: Container cannot access host network directly

### Data Security
- **Secrets Management**: API keys stored as Podman secrets
- **Encrypted Volumes**: Optional volume encryption support
- **Audit Logging**: All actions logged to systemd journal

## Management Commands

### Service Management
```bash
# Start/Stop/Restart
systemctl --user start design-team-pod.service
systemctl --user stop design-team-pod.service
systemctl --user restart design-team-pod.service

# Enable/Disable auto-start
systemctl --user enable design-team-pod.service
systemctl --user disable design-team-pod.service

# Check status
systemctl --user status design-team-pod.service
```

### Container Management
```bash
# View container details
podman inspect design-team-pod

# Access container shell
podman exec -it design-team-pod /bin/bash

# View resource usage
podman stats design-team-pod

# View logs
podman logs design-team-pod
journalctl --user -u design-team-pod.service
```

### Data Management
```bash
# Backup workspace
tar -czf design-team-backup-$(date +%Y%m%d).tar.gz /data/design-team/

# Clean old projects
find /data/design-team/workspace/projects -mtime +30 -type d -exec rm -rf {} \;

# Monitor disk usage
du -sh /data/design-team/*
```

## API Usage

### Authentication
```bash
# Currently no authentication required for localhost access
# For production, configure reverse proxy with authentication

# Example with nginx basic auth:
curl -u username:password http://proxy.example.com/design-team/health
```

### Common Operations

#### Content Scraping
```bash
# Scrape website for analysis
curl -X POST "http://127.0.0.1:8081/scrape/" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "auth": "username:password",
    "options": {
      "extract_computed_styles": true,
      "download_assets": true
    }
  }'
```

#### Image Comparison
```bash
# Compare two screenshots
curl -X POST "http://127.0.0.1:8081/compare/" \
  -F "image1=@production_screenshot.png" \
  -F "image2=@development_screenshot.png" \
  -F "ai_provider=anthropic" \
  -F "options={}"
```

#### AI Analysis
```bash
# Analyze design quality
curl -X POST "http://127.0.0.1:8081/ai-analyze/" \
  -F "image=@design_screenshot.png" \
  -F "provider=all" \
  -F "prompt=Analyze typography and layout quality"
```

#### Task Management
```bash
# Check task status
TASK_ID="task_12345_abcd"
curl "http://127.0.0.1:8081/tasks/$TASK_ID"

# List all tasks
curl "http://127.0.0.1:8081/tasks/"
```

## Monitoring & Alerting

### Health Checks
```bash
# Automated health monitoring
curl -f http://127.0.0.1:8081/health

# Expected response:
{
  "status": "healthy",
  "timestamp": 1625097600,
  "workspace": "/app/workspace",
  "disk_usage": {
    "total_gb": 100.0,
    "used_gb": 15.2,
    "free_gb": 84.8,
    "usage_percent": 15.2
  }
}
```

### Log Monitoring
```bash
# Monitor for errors
journalctl --user -u design-team-pod.service | grep ERROR

# Monitor API access
journalctl --user -u design-team-pod.service | grep "POST\|GET"

# Monitor resource usage
podman stats design-team-pod --no-stream
```

### Alerting Setup
```bash
# Example systemd alert for service failure
# /etc/systemd/system/design-team-alert@.service
[Unit]
Description=Design Team Pod Alert
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/send-alert.sh "Design Team Pod service failed: %i"

[Install]
WantedBy=multi-user.target

# Enable alerts
sudo systemctl enable design-team-alert@design-team-pod.service
```

## Backup & Recovery

### Backup Strategy
```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backup/design-team"
DATE=$(date +%Y%m%d)

# Create backup
tar -czf "$BACKUP_DIR/design-team-$DATE.tar.gz" \
  /data/design-team/workspace \
  /data/design-team/knowledge \
  /data/design-team/config

# Rotate old backups (keep 30 days)
find "$BACKUP_DIR" -name "design-team-*.tar.gz" -mtime +30 -delete

# Verify backup
tar -tzf "$BACKUP_DIR/design-team-$DATE.tar.gz" > /dev/null
```

### Recovery Procedure
```bash
# Stop service
systemctl --user stop design-team-pod.service

# Restore from backup
BACKUP_FILE="/backup/design-team/design-team-20231201.tar.gz"
sudo rm -rf /data/design-team/*
sudo tar -xzf "$BACKUP_FILE" -C /
sudo chown -R $(id -u):$(id -g) /data/design-team

# Restart service
systemctl --user start design-team-pod.service
```

## Scaling & Performance

### Horizontal Scaling
```bash
# Run multiple instances on different ports
cp design-team.container design-team-2.container
# Edit port mapping: PublishPort=127.0.0.1:8082:8080

# Deploy additional instance
systemctl --user start design-team-2.service
```

### Performance Tuning
```bash
# Increase memory limits in design-team.container
Memory=8G

# Adjust CPU limits
CPUs=4.0

# Configure workspace on faster storage
# Mount SSD volume for /data/design-team/workspace
```

### Load Balancing
```bash
# Example nginx upstream configuration
upstream design_team {
    server 127.0.0.1:8081;
    server 127.0.0.1:8082;
    server 127.0.0.1:8083;
}

server {
    listen 80;
    server_name design-team.internal.company.com;
    
    location / {
        proxy_pass http://design_team;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
journalctl --user -u design-team-pod.service

# Common causes:
# - Port already in use
# - Volume mount permissions
# - Missing dependencies

# Solutions:
sudo netstat -tlnp | grep 8081  # Check port usage
sudo chown -R $(id -u):$(id -g) /data/design-team  # Fix permissions
./test-deployment.sh  # Validate setup
```

#### API Not Responding
```bash
# Check container status
podman ps | grep design-team-pod

# Check port binding
podman port design-team-pod

# Test connectivity
curl -v http://127.0.0.1:8081/health
```

#### High Memory Usage
```bash
# Check current usage
podman stats design-team-pod

# Clear workspace cache
rm -rf /data/design-team/workspace/cache/*
rm -rf /data/design-team/workspace/temp/*

# Restart container
systemctl --user restart design-team-pod.service
```

#### AI Analysis Fails
```bash
# Check API keys
podman exec design-team-pod env | grep API_KEY

# Recreate secrets
echo -n "$ANTHROPIC_API_KEY" | podman secret create anthropic-key -
systemctl --user restart design-team-pod.service
```

### Debug Mode
```bash
# Run container with debug logging
podman run --rm -it \
  -e LOG_LEVEL=debug \
  -v /data/design-team/workspace:/app/workspace:Z \
  design-team-pod:latest \
  python -m uvicorn api.main:app --host 0.0.0.0 --log-level debug
```

## Upgrading

### Version Updates
```bash
# Pull latest code
cd /srv/xwander-platform/tools/design-team-pod
git pull

# Rebuild and deploy
./deploy.sh

# Verify upgrade
curl http://127.0.0.1:8081/ | jq '.version'
```

### Migration Procedure
```bash
# Backup current deployment
tar -czf design-team-backup-pre-upgrade.tar.gz /data/design-team/

# Stop current service
systemctl --user stop design-team-pod.service

# Deploy new version
./deploy.sh

# Verify deployment
./test-deployment.sh

# If issues, rollback:
# systemctl --user stop design-team-pod.service
# Restore backup and restart old version
```

## Production Checklist

### Pre-Deployment
- [ ] System requirements met
- [ ] Podman installed and configured
- [ ] User systemd services enabled
- [ ] API keys configured
- [ ] Test deployment successful
- [ ] Backup strategy in place
- [ ] Monitoring configured

### Post-Deployment
- [ ] Service running and healthy
- [ ] API endpoints responding
- [ ] All tools functional
- [ ] Security features validated
- [ ] Performance acceptable
- [ ] Backup tested
- [ ] Documentation updated
- [ ] Team trained on usage

### Security Review
- [ ] Container running rootless
- [ ] Read-only filesystem enabled
- [ ] Capabilities properly dropped
- [ ] Network access restricted
- [ ] Secrets properly managed
- [ ] Audit logging enabled
- [ ] Regular security updates planned

---

**Design Team Pod Deployment Guide v1.0** - Complete production deployment documentation for the pixel-perfect design toolkit.