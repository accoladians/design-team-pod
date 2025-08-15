# Design Team Pod Tool Usage Guide

## Available Tools

### 1. Visual Diff Analyzer (`visual_diff.py`)
**Purpose**: Quantitative visual comparison using multiple metrics
**Usage**:
```bash
# Basic comparison
python visual_diff.py image1.png image2.png

# With AI analysis
python visual_diff.py image1.png image2.png --ai-provider anthropic

# Custom workspace
python visual_diff.py image1.png image2.png --workspace /custom/path
```

**Output**:
- SSIM, PSNR, MAE scores
- Difference images
- AI analysis
- Accuracy recommendations

### 2. Content Scraper (`scrape_content.py`)
**Purpose**: Complete website content extraction for pixel-perfect cloning
**Usage**:
```bash
# Basic scraping
python scrape_content.py https://example.com

# With authentication
python scrape_content.py https://example.com --auth user:password

# Custom workspace
python scrape_content.py https://example.com --workspace /custom/path
```

**Output**:
- HTML content and structure
- All images and assets
- Computed styles from browser
- Screenshots at multiple resolutions
- Structured metadata

### 3. AI Analyzer (`ai_analyzer.py`)
**Purpose**: AI-powered visual analysis and recommendations
**Usage**:
```bash
# Single image analysis
python ai_analyzer.py image.png --provider anthropic

# Image comparison
python ai_analyzer.py image1.png --compare image2.png

# All providers
python ai_analyzer.py image.png --provider all

# Custom prompt
python ai_analyzer.py image.png --prompt "Analyze typography and spacing"
```

**Output**:
- Design quality assessment
- UX recommendations
- Accessibility evaluation
- Pixel-perfect accuracy scoring

## Complete Workflow

### Step 1: Content Extraction
```bash
# Scrape production site
python scrape_content.py https://production-site.com --auth user:pass

# This creates:
# - /workspace/projects/production_site_com_[timestamp]/
#   - content/         # HTML and text
#   - images/          # All images
#   - styles/          # CSS files and computed styles
#   - screenshots/     # Full page screenshots
#   - data/           # Structured content JSON
```

### Step 2: Implementation
Using the scraped content:
1. Import exact text content from `data/content.json`
2. Use production images from `images/`
3. Apply computed styles from `styles/computed_styles.json`
4. Match layout using screenshot references

### Step 3: Validation
```bash
# Take screenshot of your implementation
python scrape_content.py https://your-dev-site.com --auth dev:password

# Compare with production
python visual_diff.py production_screenshot.png dev_screenshot.png --ai-provider all

# Get detailed AI analysis
python ai_analyzer.py dev_screenshot.png --compare production_screenshot.png
```

### Step 4: Iteration
Based on analysis results:
1. Review recommendations from AI analysis
2. Fix issues with highest impact scores
3. Re-test specific components
4. Repeat until SSIM > 0.9

## API Usage

### Start API Server
```bash
# In container
python /app/api/main.py

# Or via uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8080
```

### API Endpoints

#### Scrape Content
```bash
curl -X POST "http://localhost:8080/scrape/" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "auth": "user:pass"}'
```

#### Compare Images
```bash
curl -X POST "http://localhost:8080/compare/" \
  -F "image1=@production.png" \
  -F "image2=@development.png" \
  -F "ai_provider=anthropic"
```

#### AI Analysis
```bash
curl -X POST "http://localhost:8080/ai-analyze/" \
  -F "image=@screenshot.png" \
  -F "provider=all" \
  -F "prompt=Analyze design quality and UX"
```

#### Check Task Status
```bash
curl "http://localhost:8080/tasks/task_12345"
```

## Best Practices

### 1. Content-First Workflow
- Always scrape real content before building
- Extract computed styles, not approximated ones
- Use production assets, not placeholders

### 2. Quantitative Validation
- Aim for SSIM > 0.9 for pixel-perfect
- Use multiple validation tools
- Cross-validate with AI analysis

### 3. Systematic Iteration
- Test component by component
- Fix highest-impact issues first
- Re-validate after each change

### 4. Security Considerations
- Use authentication for private sites
- Store credentials securely
- Clean up temporary files

## Troubleshooting

### Common Issues

#### Tool Not Found
```bash
# Check tool availability
python -c "from visual_diff import VisualDiffAnalyzer; print('OK')"

# Fix permissions
chmod +x /app/tools/*.py
```

#### Authentication Fails
```bash
# Test auth directly
curl -u user:pass https://example.com

# Check base64 encoding
echo -n "user:pass" | base64
```

#### Low Accuracy Scores
1. Check content extraction completeness
2. Verify asset loading (images, fonts)
3. Compare computed styles vs applied styles
4. Validate responsive breakpoints

#### AI Analysis Fails
1. Check API key environment variables
2. Verify image format (PNG recommended)
3. Check image size limits
4. Review provider-specific requirements

## Performance Tips

### 1. Efficient Scraping
- Use specific selectors for targeted content
- Cache downloaded assets
- Compress large images

### 2. Faster Comparison
- Resize images to consistent dimensions
- Use appropriate compression
- Batch multiple comparisons

### 3. Resource Management
- Clean up temporary files
- Monitor workspace disk usage
- Use appropriate timeouts

## Environment Variables

Required for AI analysis:
```bash
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key  # For Gemini (future)
```

Optional configuration:
```bash
WORKSPACE_DIR=/app/workspace
TOOLS_DIR=/app/tools
KNOWLEDGE_DIR=/app/knowledge
API_HOST=0.0.0.0
API_PORT=8080
LOG_LEVEL=info
```

## Integration Examples

### GitHub Actions
```yaml
- name: Run Pixel-Perfect Validation
  run: |
    python scrape_content.py ${{ env.PRODUCTION_URL }}
    python scrape_content.py ${{ env.STAGING_URL }}
    python visual_diff.py prod_screenshot.png staging_screenshot.png
```

### CI/CD Pipeline
```bash
#!/bin/bash
# Automated validation script

PROD_URL="https://production.com"
DEV_URL="https://development.com"

# Scrape both sites
python scrape_content.py $PROD_URL --workspace ./validation
python scrape_content.py $DEV_URL --workspace ./validation

# Find screenshots
PROD_SCREENSHOT=$(find ./validation -name "*production*" -name "*.png" | head -1)
DEV_SCREENSHOT=$(find ./validation -name "*development*" -name "*.png" | head -1)

# Compare
python visual_diff.py $PROD_SCREENSHOT $DEV_SCREENSHOT --output-format json > results.json

# Check accuracy
ACCURACY=$(jq '.summary.overall_accuracy' results.json)
if (( $(echo "$ACCURACY > 90" | bc -l) )); then
  echo "✅ Pixel-perfect validation passed: $ACCURACY%"
  exit 0
else
  echo "❌ Pixel-perfect validation failed: $ACCURACY%"
  exit 1
fi
```

---

*Design Team Pod v2.0.0 - Complete pixel-perfect cloning toolkit*