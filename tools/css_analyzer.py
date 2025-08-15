#!/usr/bin/env python3
"""
CSS Difference Analyzer v0.1.1 - Design Team Pod
Analyzes CSS differences between production and implementation
"""

import json
import argparse
from pathlib import Path
import re
from difflib import SequenceMatcher

class CSSAnalyzer:
    def __init__(self, output_dir="css_analysis"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Critical CSS properties for pixel-perfect matching
        self.critical_properties = {
            'layout': ['display', 'position', 'width', 'height', 'top', 'left', 'right', 'bottom'],
            'spacing': ['margin', 'marginTop', 'marginRight', 'marginBottom', 'marginLeft',
                       'padding', 'paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft'],
            'typography': ['fontFamily', 'fontSize', 'fontWeight', 'lineHeight', 'letterSpacing', 'textAlign'],
            'background': ['backgroundColor', 'backgroundImage', 'backgroundSize', 'backgroundPosition'],
            'border': ['border', 'borderRadius', 'borderWidth', 'borderColor'],
            'flexbox': ['flexDirection', 'justifyContent', 'alignItems', 'gap', 'flexWrap'],
            'grid': ['gridTemplateColumns', 'gridTemplateRows', 'gridGap']
        }
    
    def analyze_extracted_styles(self, production_data_path, sandbox_data_path=None):
        """Analyze CSS differences from extracted data"""
        print(f"🔍 Analyzing CSS differences...")
        
        # Load production data
        with open(production_data_path, 'r') as f:
            production_data = json.load(f)
        
        production_styles = production_data.get('computed_styles', {})
        production_structure = production_data.get('component_structure', {})
        
        analysis = {
            'metadata': {
                'production_elements': len(production_styles),
                'analyzer_version': '0.1.1'
            },
            'critical_missing_styles': [],
            'typography_issues': [],
            'layout_problems': [],
            'spacing_inconsistencies': [],
            'missing_components': [],
            'recommendations': []
        }
        
        # Analyze critical styles
        self._analyze_critical_styles(production_styles, analysis)
        
        # Analyze component structure
        self._analyze_component_structure(production_structure, analysis)
        
        # Generate actionable recommendations
        self._generate_recommendations(analysis)
        
        # Save analysis
        self._save_analysis(analysis)
        
        return analysis
    
    def _analyze_critical_styles(self, production_styles, analysis):
        """Analyze critical CSS properties that affect pixel-perfect accuracy"""
        print("🎨 Analyzing critical CSS properties...")
        
        # Group elements by type for better analysis
        layout_elements = {}
        typography_elements = {}
        
        for element_id, element_data in production_styles.items():
            styles = element_data.get('styles', {})
            tag = element_data.get('tag', '').lower()
            className = element_data.get('className', '')
            
            # Analyze layout-critical elements
            if styles.get('display') in ['flex', 'grid', 'block'] and styles.get('height', '0px') != '0px':
                layout_elements[element_id] = {
                    'tag': tag,
                    'className': className,
                    'display': styles.get('display'),
                    'width': styles.get('width'),
                    'height': styles.get('height'),
                    'position': styles.get('position'),
                    'margin': styles.get('margin'),
                    'padding': styles.get('padding'),
                    'priority': self._calculate_priority(tag, className, styles)
                }
            
            # Analyze typography elements
            if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'span', 'a'] or 'text' in className.lower():
                typography_elements[element_id] = {
                    'tag': tag,
                    'className': className,
                    'fontFamily': styles.get('fontFamily'),
                    'fontSize': styles.get('fontSize'),
                    'fontWeight': styles.get('fontWeight'),
                    'lineHeight': styles.get('lineHeight'),
                    'color': styles.get('color'),
                    'priority': self._calculate_priority(tag, className, styles)
                }
        
        # Find critical missing styles
        high_priority_elements = []
        for element_id, element in layout_elements.items():
            if element['priority'] >= 8:  # High priority threshold
                high_priority_elements.append({
                    'element_id': element_id,
                    'type': 'layout',
                    'styles': element,
                    'issue': 'Critical layout element - must match exactly'
                })
        
        for element_id, element in typography_elements.items():
            if element['priority'] >= 7:  # High priority threshold for text
                high_priority_elements.append({
                    'element_id': element_id,
                    'type': 'typography',
                    'styles': element,
                    'issue': 'Important typography - affects visual hierarchy'
                })
        
        analysis['critical_missing_styles'] = high_priority_elements
    
    def _analyze_component_structure(self, production_structure, analysis):
        """Analyze component structure for missing sections"""
        print("🧩 Analyzing component structure...")
        
        sections = production_structure.get('sections', [])
        page_height = production_structure.get('pageHeight', 0)
        
        # Identify major sections that must be present
        major_sections = []
        for section in sections:
            if section.get('boundingRect', {}).get('height', 0) > 200:  # Significant height
                major_sections.append({
                    'tag': section.get('tag'),
                    'className': section.get('className'),
                    'id': section.get('id'),
                    'height': section.get('boundingRect', {}).get('height'),
                    'content_preview': section.get('textContent', '')[:100],
                    'importance': 'high' if section.get('boundingRect', {}).get('height', 0) > 500 else 'medium'
                })
        
        analysis['missing_components'] = major_sections
        analysis['metadata']['expected_page_height'] = page_height
        analysis['metadata']['major_sections_count'] = len(major_sections)
    
    def _calculate_priority(self, tag, className, styles):
        """Calculate priority score for CSS element (0-10)"""
        priority = 0
        
        # Tag-based priority
        if tag in ['header', 'main', 'footer', 'nav']:
            priority += 3
        elif tag in ['section', 'article']:
            priority += 2
        elif tag in ['h1', 'h2', 'h3']:
            priority += 2
        elif tag == 'h1':
            priority += 1  # Extra for h1
        
        # Class-based priority
        if className:
            class_lower = className.lower()
            if any(keyword in class_lower for keyword in ['hero', 'header', 'main', 'footer']):
                priority += 3
            elif any(keyword in class_lower for keyword in ['section', 'container', 'wrapper']):
                priority += 2
            elif any(keyword in class_lower for keyword in ['title', 'heading']):
                priority += 1
        
        # Style-based priority
        if styles.get('position') in ['fixed', 'absolute']:
            priority += 1
        if styles.get('display') in ['flex', 'grid']:
            priority += 1
        
        height = styles.get('height', '0px')
        if height and height != '0px' and height != 'auto':
            try:
                height_val = float(re.findall(r'\d+', height)[0]) if re.findall(r'\d+', height) else 0
                if height_val > 200:
                    priority += 2
                elif height_val > 100:
                    priority += 1
            except:
                pass
        
        return min(priority, 10)  # Cap at 10
    
    def _generate_recommendations(self, analysis):
        """Generate actionable recommendations"""
        print("💡 Generating recommendations...")
        
        recommendations = []
        
        # Missing sections recommendations
        if analysis['missing_components']:
            major_missing = [comp for comp in analysis['missing_components'] if comp['importance'] == 'high']
            if major_missing:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Missing Sections',
                    'issue': f"Missing {len(major_missing)} major sections causing height difference",
                    'action': 'Add missing sections to match production layout',
                    'sections': [comp['className'] or comp['tag'] for comp in major_missing],
                    'estimated_impact': '+' + str(sum(comp['height'] for comp in major_missing)) + 'px height'
                })
        
        # Critical styles recommendations
        critical_layout = [style for style in analysis['critical_missing_styles'] if style['type'] == 'layout']
        if critical_layout:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Layout Styles',
                'issue': f"{len(critical_layout)} critical layout elements need exact CSS matching",
                'action': 'Apply computed styles from production to match layout exactly',
                'elements': [style['styles']['className'] or style['styles']['tag'] for style in critical_layout[:5]]
            })
        
        # Typography recommendations
        critical_typography = [style for style in analysis['critical_missing_styles'] if style['type'] == 'typography']
        if critical_typography:
            font_families = set()
            for style in critical_typography:
                font_family = style['styles'].get('fontFamily', '')
                if font_family and font_family != 'inherit':
                    font_families.add(font_family.split(',')[0].strip('"\''))
            
            if font_families:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Typography',
                    'issue': f"Typography doesn't match production fonts",
                    'action': 'Load production fonts and apply exact font sizes/weights',
                    'fonts_needed': list(font_families)
                })
        
        # Quick wins
        if analysis['metadata']['expected_page_height'] > 0:
            current_estimated = 1800  # Rough current height
            missing_height = analysis['metadata']['expected_page_height'] - current_estimated
            if missing_height > 1000:
                recommendations.append({
                    'priority': 'HIGH',
                    'category': 'Quick Win',
                    'issue': f"Page too short by ~{missing_height}px",
                    'action': 'Focus on adding the largest missing sections first',
                    'quick_fix': 'Add anchor navigation and extend itinerary/FAQ sections'
                })
        
        analysis['recommendations'] = recommendations
    
    def _save_analysis(self, analysis):
        """Save analysis results"""
        print("💾 Saving CSS analysis...")
        
        # Save detailed JSON
        with open(self.output_dir / "css_analysis.json", 'w') as f:
            json.dump(analysis, f, indent=2)
        
        # Generate readable report
        self._generate_readable_report(analysis)
        
        print(f"✅ Analysis saved to {self.output_dir}")
    
    def _generate_readable_report(self, analysis):
        """Generate human-readable report"""
        report = []
        report.append("# CSS Analysis Report v0.1.1\n")
        
        # Metadata
        meta = analysis['metadata']
        report.append(f"## Analysis Summary")
        report.append(f"- Production elements analyzed: {meta['production_elements']}")
        report.append(f"- Expected page height: {meta.get('expected_page_height', 'unknown')}px")
        report.append(f"- Major sections expected: {meta.get('major_sections_count', 'unknown')}\n")
        
        # Recommendations (most important)
        if analysis['recommendations']:
            report.append(f"## 🎯 Priority Recommendations")
            for i, rec in enumerate(analysis['recommendations'], 1):
                report.append(f"\n### {i}. {rec['category']} ({rec['priority']})")
                report.append(f"**Issue**: {rec['issue']}")
                report.append(f"**Action**: {rec['action']}")
                
                if 'sections' in rec:
                    report.append(f"**Missing sections**: {', '.join(rec['sections'])}")
                if 'elements' in rec:
                    report.append(f"**Key elements**: {', '.join(rec['elements'])}")
                if 'fonts_needed' in rec:
                    report.append(f"**Fonts needed**: {', '.join(rec['fonts_needed'])}")
                if 'estimated_impact' in rec:
                    report.append(f"**Impact**: {rec['estimated_impact']}")
                if 'quick_fix' in rec:
                    report.append(f"**Quick fix**: {rec['quick_fix']}")
        
        # Critical missing styles
        if analysis['critical_missing_styles']:
            report.append(f"\n## 🎨 Critical Style Elements ({len(analysis['critical_missing_styles'])})")
            layout_count = len([s for s in analysis['critical_missing_styles'] if s['type'] == 'layout'])
            typography_count = len([s for s in analysis['critical_missing_styles'] if s['type'] == 'typography'])
            report.append(f"- Layout elements: {layout_count}")
            report.append(f"- Typography elements: {typography_count}")
        
        # Missing components
        if analysis['missing_components']:
            report.append(f"\n## 🧩 Missing Components ({len(analysis['missing_components'])})")
            for comp in analysis['missing_components'][:5]:  # Top 5
                report.append(f"- **{comp['className'] or comp['tag']}** "
                            f"({comp['height']}px tall, {comp['importance']} priority)")
        
        # Save report
        with open(self.output_dir / "css_analysis_report.md", 'w') as f:
            f.write('\n'.join(report))

def main():
    parser = argparse.ArgumentParser(description='CSS Difference Analyzer v0.1.1')
    parser.add_argument('production_data', help='Path to production extracted data JSON')
    parser.add_argument('-o', '--output', default='css_analysis', help='Output directory')
    
    args = parser.parse_args()
    
    analyzer = CSSAnalyzer(output_dir=args.output)
    results = analyzer.analyze_extracted_styles(args.production_data)
    
    print(f"\n📊 Analysis Summary:")
    print(f"   Critical style elements: {len(results['critical_missing_styles'])}")
    print(f"   Missing components: {len(results['missing_components'])}")
    print(f"   Priority recommendations: {len(results['recommendations'])}")
    print(f"   Report: {Path(args.output) / 'css_analysis_report.md'}")

if __name__ == "__main__":
    main()