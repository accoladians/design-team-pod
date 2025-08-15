# Design Team Pod

**Version 2.0.0** - Production-ready pixel-perfect cloning toolkit in a secure, portable container.

## Overview

The Design Team Pod is a comprehensive containerized solution for pixel-perfect website cloning and design analysis. It packages advanced visual diff tools, AI-powered analysis, and systematic workflows into a secure, portable container that can be deployed anywhere with Podman.

## Features

### 🔧 Core Tools
- **Visual Diff Analyzer** - Multi-metric image comparison (SSIM, PSNR, MAE)
- **Content Scraper** - Complete website content extraction with computed styles
- **AI Analyzer** - Multi-provider AI analysis (OpenAI, Anthropic, Gemini)
- **REST API** - Full HTTP API for remote usage

### 🔒 Security First
- Rootless container operation
- Minimal attack surface (drop all capabilities)
- Read-only filesystem with targeted volume mounts
- SELinux/AppArmor compatible
- Secrets management for API keys

### 📦 Portable & Scalable
- Self-contained with all dependencies
- Quadlet systemd integration
- Persistent knowledge base
- Resource limits and monitoring
- Easy deployment and management

### 🧠 AI-Powered Analysis
- OpenAI GPT-4V integration
- Anthropic Claude 3 Sonnet
- Multi-provider comparison
- Structured design feedback
- Pixel-perfect accuracy scoring

## 🤖 Quick Agent Onboarding

**New Agent? Start here!** Everything you need to utilize the Design Team toolkit.

### Instant Usage (No Setup Required)
```bash
# You're already here! Use tools directly:
cd /srv/xwander-platform/tools/design-team-pod/tools/

# Compare two images with multiple metrics
python3 visual_diff.py image1.png image2.png

# Scrape website content and styles
python3 scrape_content.py https://example.com -o output/

# AI analysis of designs
python3 ai_analyzer.py screenshot.png "Analyze this design"
```

### Available Tools & Usage
- **`visual_diff.py`** - Multi-metric comparison (SSIM, PSNR, MAE, AI analysis)
- **`scrape_content.py`** - Complete content extraction with computed styles
- **`ai_analyzer.py`** - Multi-provider AI analysis (OpenAI, Anthropic, Gemini)

### Knowledge Base Access
- **Lessons Learned**: `knowledge/pixel-perfect-lessons.md`
- **Tool Guides**: `knowledge/visual-diff-guide.md`
- **Best Practices**: `knowledge/workflows/`

### Container Deployment (Optional)
Only needed for API access or team sharing.

## Quick Start

### Prerequisites
- Podman 3.4+ installed
- User systemd services enabled
- 5GB+ available disk space
- API keys for AI providers (optional but recommended)

### Deployment

```bash
# Clone or copy the design-team-pod directory
cd /srv/xwander-platform/tools/design-team-pod

# Set environment variables (optional)
export ANTHROPIC_API_KEY="your_anthropic_key"
export OPENAI_API_KEY="your_openai_key"

# Deploy the pod
./deploy.sh

# Check status
systemctl --user status design-team-pod.service
```

### Usage

#### API Access
```bash
# Health check
curl http://127.0.0.1:8081/health

# API documentation
open http://127.0.0.1:8081/docs
```

#### Direct Tool Usage
```bash
# Enter container shell
podman exec -it design-team-pod /bin/bash

# Run tools directly
python visual_diff.py image1.png image2.png
python scrape_content.py https://example.com
python ai_analyzer.py screenshot.png --provider anthropic
```

## Architecture

```
Design Team Pod
├── API Layer (FastAPI)
│   ├── /scrape/ - Content extraction endpoints
│   ├── /compare/ - Image comparison endpoints
│   ├── /ai-analyze/ - AI analysis endpoints
│   └── /tasks/ - Background task management
├── Core Tools
│   ├── visual_diff.py - Multi-metric comparison
│   ├── scrape_content.py - Content extraction
│   └── ai_analyzer.py - AI-powered analysis
├── Knowledge Base
│   ├── Pixel-perfect lessons learned
│   ├── Tool usage guides
│   └── Best practices documentation
└── Persistent Storage
    ├── /workspace/ - Project data
    ├── /knowledge/ - Documentation
    └── /config/ - Configuration files
```

## Tool Documentation

### Visual Diff Analyzer
```bash
# Compare two images with all metrics
python visual_diff.py production.png development.png

# Include AI analysis
python visual_diff.py prod.png dev.png --ai-provider anthropic

# Output JSON for automation
python visual_diff.py prod.png dev.png --output-format json
```

**Metrics Provided:**
- SSIM (Structural Similarity Index) - Target: >0.9 for pixel-perfect
- PSNR (Peak Signal-to-Noise Ratio) - Target: >30dB
- MAE (Mean Absolute Error) - Target: <5%
- AI quality assessment and recommendations

### Content Scraper
```bash
# Comprehensive site scraping
python scrape_content.py https://production-site.com

# With authentication
python scrape_content.py https://site.com --auth user:password

# Custom workspace
python scrape_content.py https://site.com --workspace /custom/path
```

**Extracted Data:**
- Complete HTML content and structure
- All images, CSS, and JavaScript assets
- Computed styles from browser rendering
- Multiple viewport screenshots
- Structured metadata and navigation

### AI Analyzer
```bash
# Single image analysis
python ai_analyzer.py screenshot.png --provider anthropic

# Image comparison
python ai_analyzer.py original.png --compare replica.png

# All AI providers
python ai_analyzer.py image.png --provider all

# Custom analysis prompt
python ai_analyzer.py image.png --prompt "Focus on typography and spacing"
```

**AI Capabilities:**
- Design quality assessment (1-100 score)
- UX and accessibility evaluation
- Pixel-perfect accuracy analysis
- Specific improvement recommendations
- Cross-provider validation

## API Reference

### Scrape Content
```bash
POST /scrape/
{
  "url": "https://example.com",
  "auth": "user:password",
  "options": {
    "extract_computed_styles": true,
    "download_assets": true
  }
}
```

### Compare Images
```bash
POST /compare/
Content-Type: multipart/form-data
- image1: [PNG file]
- image2: [PNG file]  
- ai_provider: "anthropic"
- options: "{}"
```

### AI Analysis
```bash
POST /ai-analyze/
Content-Type: multipart/form-data
- image: [PNG file]
- provider: "all"
- prompt: "Analyze design quality"
- options: "{}"
```

### Task Management
```bash
GET /tasks/{task_id}        # Get task status
GET /tasks/                 # List all tasks
DELETE /tasks/{task_id}     # Cancel/remove task
```

## Configuration

### Environment Variables
```bash
# Required for AI analysis
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key

# Optional configuration
WORKSPACE_DIR=/app/workspace
API_HOST=0.0.0.0
API_PORT=8080
LOG_LEVEL=info
```

### Volume Mounts
```bash
# Persistent data locations
/data/design-team/workspace/    # Project data and results
/data/design-team/knowledge/    # Documentation and lessons
/data/design-team/config/       # Configuration files
```

## Management Commands

```bash
# Service management
systemctl --user start design-team-pod.service
systemctl --user stop design-team-pod.service
systemctl --user restart design-team-pod.service
systemctl --user status design-team-pod.service

# Logs and monitoring
journalctl --user -u design-team-pod.service -f
podman stats design-team-pod

# Container access
podman exec -it design-team-pod /bin/bash
podman inspect design-team-pod
```

## Pixel-Perfect Workflow

### 1. Extract Production Content
```bash
# Scrape production site
curl -X POST "http://127.0.0.1:8081/scrape/" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://production.com", "auth": "user:pass"}'
```

### 2. Implement with Scraped Data
- Use exact text content from extraction
- Apply computed styles, not approximated ones
- Load production images and assets
- Match exact layout measurements

### 3. Validate Implementation
```bash
# Take screenshot of implementation
curl -X POST "http://127.0.0.1:8081/scrape/" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://development.com"}'

# Compare with production
curl -X POST "http://127.0.0.1:8081/compare/" \
  -F "image1=@production_screenshot.png" \
  -F "image2=@development_screenshot.png" \
  -F "ai_provider=anthropic"
```

### 4. Iterate Based on Analysis
- Review AI recommendations
- Fix highest-impact discrepancies
- Re-validate until SSIM > 0.9

## Accuracy Targets

| Level | SSIM Score | Quality |
|-------|------------|---------|
| Pixel-Perfect | >0.95 | Production ready |
| High Accuracy | >0.85 | Minor adjustments needed |
| Good Accuracy | >0.75 | Significant work required |
| Acceptable | >0.65 | Major revision needed |
| Poor | <0.65 | Start over |

## Security Considerations

### Container Security
- Runs as non-root user (UID 1000)
- All capabilities dropped except NET_BIND_SERVICE
- Read-only root filesystem
- No new privileges flag set
- SELinux labels applied

### Data Security
- API keys stored as Podman secrets
- Temporary files in memory-backed filesystems
- Isolated network namespace
- Regular security updates via base image

### Access Control
- API bound to localhost only by default
- Basic authentication support
- Rate limiting enabled
- CORS configured for trusted domains

## Troubleshooting

### Common Issues

#### Pod Won't Start
```bash
# Check logs
journalctl --user -u design-team-pod.service

# Verify image
podman images | grep design-team-pod

# Check prerequisites
./deploy.sh help
```

#### API Not Responding
```bash
# Check port binding
podman port design-team-pod

# Test network connectivity
curl -v http://127.0.0.1:8081/health

# Check container status
podman ps -a | grep design-team-pod
```

#### Low Accuracy Scores
1. Verify content extraction is complete
2. Check all assets are loading correctly
3. Compare computed styles vs applied styles
4. Validate font loading and rendering

#### AI Analysis Fails
1. Check API key environment variables
2. Verify image format (PNG recommended)
3. Check image size limits (50MB max)
4. Review provider-specific error messages

### Debug Mode
```bash
# Run with debug logging
podman run --rm -it \
  -e LOG_LEVEL=debug \
  -v design-team-workspace:/app/workspace:Z \
  localhost/design-team-pod:latest \
  python -m uvicorn api.main:app --host 0.0.0.0 --log-level debug
```

## Performance Tuning

### Resource Limits
```bash
# Default limits (configurable in Quadlet)
Memory: 4GB
CPU: 2 cores
PIDs: 200
Disk: Unlimited (monitor via alerts)
```

### Optimization Tips
- Use appropriate image compression
- Batch multiple analyses
- Clean up old project data regularly
- Monitor workspace disk usage

## Integration Examples

### CI/CD Pipeline
```bash
#!/bin/bash
# Automated pixel-perfect validation

# Start design team pod
curl -X POST "http://design-team:8081/scrape/" \
  -d '{"url": "'$PRODUCTION_URL'"}'

curl -X POST "http://design-team:8081/scrape/" \
  -d '{"url": "'$STAGING_URL'"}'

# Compare results
RESULT=$(curl -X POST "http://design-team:8081/compare/" \
  -F "image1=@prod.png" \
  -F "image2=@staging.png" | jq '.accuracy_score')

if (( $(echo "$RESULT > 90" | bc -l) )); then
  echo "✅ Pixel-perfect validation passed: $RESULT%"
else
  echo "❌ Validation failed: $RESULT%"
  exit 1
fi
```

### GitHub Actions
```yaml
- name: Pixel-Perfect Validation
  run: |
    docker run --rm \
      -v ${{ github.workspace }}:/workspace \
      design-team-pod:latest \
      python visual_diff.py prod.png staging.png
```

## Version History

### v2.0.0 (Current)
- Complete rewrite with security focus
- Quadlet systemd integration
- Multi-provider AI analysis
- REST API interface
- Persistent knowledge base
- Production-ready deployment

### v1.0.0 (Legacy)
- Basic tool collection
- Fedora-based container
- Manual deployment
- Limited AI integration

## Support & Contributing

### Documentation
- Tool usage guides in `/knowledge/`
- API documentation at `/docs`
- Configuration examples in `/config/`

### Getting Help
1. Check logs: `journalctl --user -u design-team-pod.service`
2. Review documentation in knowledge base
3. Test individual tools in container shell
4. Verify environment configuration

### Contributing
1. Follow security-first principles
2. Test all changes thoroughly
3. Update documentation
4. Maintain backward compatibility

## License

This project is part of the Xwander Platform design toolkit.

---

**Design Team Pod v2.0.0** - The complete pixel-perfect cloning solution in a secure, portable container.