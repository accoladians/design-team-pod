# 🤖 Agent Quick Start - Design Team Pod

## 📍 **You Are Here**
```
/srv/xwander-platform/tools/design-team-pod/
```

## ⚡ **Instant Commands**
```bash
# Visual comparison with multiple metrics
python3 tools/visual_diff.py production.png sandbox.png

# Website content extraction
python3 tools/scrape_content.py https://example.com

# AI design analysis  
python3 tools/ai_analyzer.py screenshot.png "What needs to be fixed?"
```

## 🎯 **Most Common Use Cases**

### 1. Pixel-Perfect Website Cloning
```bash
# Step 1: Compare current vs target
python3 tools/visual_diff.py target.png current.png -o comparison.json

# Step 2: Extract target styles
python3 tools/scrape_content.py https://target-site.com --extract-styles

# Step 3: Get AI recommendations
python3 tools/ai_analyzer.py comparison_diff.png "What CSS changes needed?"

# Step 4: Apply changes, repeat until SSIM > 0.9
```

### 2. Design Quality Analysis
```bash
# Multi-provider AI analysis
python3 tools/ai_analyzer.py design.png --provider anthropic --provider openai

# Generate improvement report
python3 tools/visual_diff.py design_v1.png design_v2.png --generate-report
```

### 3. Content Migration
```bash
# Complete site extraction
python3 tools/scrape_content.py https://old-site.com \
  --include-images --include-styles --include-computed-css

# Structured content output for developers
```

## 📊 **Understanding Results**

### Visual Diff Metrics
- **SSIM > 0.9** = Pixel-perfect (90%+ accuracy)
- **SSIM 0.8-0.9** = Very similar (80-90% accuracy)  
- **SSIM < 0.8** = Significant differences

### AI Analysis Output
- **Structured feedback** with specific recommendations
- **Priority levels** (critical, important, minor)
- **Actionable CSS changes** with exact values

## 🧠 **Knowledge Base**

### Essential Reading
- `knowledge/pixel-perfect-lessons.md` - Critical failure patterns
- `knowledge/visual-diff-guide.md` - Tool documentation
- `knowledge/workflows/` - Process templates

### Example Workflows
- `knowledge/workflows/pixel-perfect.yaml` - Complete cloning process
- `knowledge/workflows/design-analysis.yaml` - Quality assessment

## 🔧 **Tool Configuration**

### Environment Variables
```bash
# Optional but recommended for AI analysis
export ANTHROPIC_API_KEY="your_key"
export OPENAI_API_KEY="your_key" 
export GEMINI_API_KEY="your_key"
```

### Output Directories
```bash
tools/
├── visual_diff.py     # Multi-metric comparison
├── scrape_content.py  # Content extraction
└── ai_analyzer.py     # AI analysis

results/               # Outputs here
├── comparisons/       # Visual diff results
├── scraped/          # Extracted content
└── analysis/         # AI reports
```

## 🚀 **Advanced Usage**

### Container Mode (Team Sharing)
```bash
# Deploy as service for API access
./deploy.sh

# Access via REST API
curl http://localhost:8081/docs
```

### Integration Patterns
```bash
# Use in CI/CD pipelines
python3 tools/visual_diff.py prod.png staging.png --threshold 0.9

# Batch processing
for site in sites.txt; do
  python3 tools/scrape_content.py "$site"
done
```

## ❓ **Quick Help**

### Get Tool Help
```bash
python3 tools/visual_diff.py --help
python3 tools/scrape_content.py --help  
python3 tools/ai_analyzer.py --help
```

### Common Issues
- **Missing dependencies**: Run `pip install -r requirements.txt`
- **API key errors**: Set environment variables above
- **Permission issues**: Check file paths and permissions

## 🎯 **Success Patterns**

1. **Start with visual diff** to understand current state
2. **Extract production styles** before making changes  
3. **Use AI analysis** for specific recommendations
4. **Iterate systematically** until metrics show success
5. **Document learnings** in knowledge base

---

**💡 Tip**: The Design Team Pod embodies institutional knowledge - it gets smarter with each project!

**🎯 Goal**: Transform pixel-perfect cloning from art to science through systematic, measurable processes.