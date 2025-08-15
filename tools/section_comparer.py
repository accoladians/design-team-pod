#!/usr/bin/env python3
"""
Section-Level Comparison Tool v0.1.1 - Design Team Pod
Compares specific sections between production and sandbox for targeted improvements
"""

import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright
import argparse
import subprocess
import sys

class SectionComparer:
    def __init__(self, output_dir="section_comparison"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def compare_page_sections(self, production_url, sandbox_url, auth=None):
        """Compare sections between production and sandbox"""
        print(f"🔍 Section-by-section comparison:")
        print(f"   Production: {production_url}")
        print(f"   Sandbox: {sandbox_url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            if auth:
                username, password = auth.split(':')
                await context.set_http_credentials(username=username, password=password)
            
            try:
                # Load both pages
                prod_page = await context.new_page()
                sandbox_page = await context.new_page()
                
                await prod_page.goto(production_url, wait_until='networkidle')
                await sandbox_page.goto(sandbox_url, wait_until='networkidle')
                
                # Get page structure from both
                prod_sections = await self._extract_sections(prod_page, "production")
                sandbox_sections = await self._extract_sections(sandbox_page, "sandbox")
                
                # Compare sections
                comparison_results = await self._compare_sections(
                    prod_sections, sandbox_sections, prod_page, sandbox_page
                )
                
                # Save results
                self._save_comparison_results(comparison_results)
                
                return comparison_results
                
            finally:
                await browser.close()
    
    async def _extract_sections(self, page, page_type):
        """Extract identifiable sections from a page"""
        print(f"📋 Extracting {page_type} sections...")
        
        sections = await page.evaluate("""
            () => {
                const sections = [];
                
                // Look for common section identifiers
                const selectors = [
                    'header', 'nav', 'main', 'section', 'article', 'aside', 'footer',
                    '.hero-section', '.tour-single-section', '.partner-section',
                    '.container', '.content', '.wrapper', '[class*="section"]',
                    '[id*="section"]', '[id*="tour"]', '[id*="detail"]', '[id*="itinerary"]'
                ];
                
                const found = new Set(); // Avoid duplicates
                
                selectors.forEach(selector => {
                    try {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach((el, index) => {
                            const rect = el.getBoundingClientRect();
                            if (rect.height > 50 && !found.has(el)) { // Significant height
                                found.add(el);
                                
                                sections.push({
                                    selector: selector,
                                    tag: el.tagName,
                                    className: el.className,
                                    id: el.id,
                                    index: sections.length,
                                    boundingRect: {
                                        x: Math.round(rect.x),
                                        y: Math.round(rect.y),
                                        width: Math.round(rect.width),
                                        height: Math.round(rect.height)
                                    },
                                    textContent: el.textContent?.substring(0, 150) || '',
                                    childCount: el.children.length,
                                    hasBackground: window.getComputedStyle(el).backgroundColor !== 'rgba(0, 0, 0, 0)',
                                    visibility: window.getComputedStyle(el).visibility,
                                    display: window.getComputedStyle(el).display
                                });
                            }
                        });
                    } catch (e) {
                        // Skip invalid selectors
                    }
                });
                
                return sections.sort((a, b) => a.boundingRect.y - b.boundingRect.y);
            }
        """)
        
        # Take screenshots of each section
        screenshots_dir = self.output_dir / f"{page_type}_sections"
        screenshots_dir.mkdir(exist_ok=True)
        
        for i, section in enumerate(sections):
            try:
                # Try to find element by multiple methods
                element = None
                if section['id']:
                    element = await page.query_selector(f"#{section['id']}")
                elif section['className']:
                    # Try first class
                    first_class = section['className'].split()[0]
                    if first_class:
                        element = await page.query_selector(f".{first_class}")
                
                if element:
                    await element.screenshot(path=screenshots_dir / f"section_{i:02d}.png")
                    section['screenshot'] = f"{page_type}_sections/section_{i:02d}.png"
                
            except Exception as e:
                print(f"Failed to screenshot section {i}: {e}")
                section['screenshot'] = None
        
        return sections
    
    async def _compare_sections(self, prod_sections, sandbox_sections, prod_page, sandbox_page):
        """Compare sections between production and sandbox"""
        print(f"⚖️  Comparing sections...")
        
        # Basic metrics
        comparison = {
            'metadata': {
                'production_sections': len(prod_sections),
                'sandbox_sections': len(sandbox_sections),
                'section_count_match': len(prod_sections) == len(sandbox_sections)
            },
            'missing_sections': [],
            'height_differences': [],
            'content_differences': [],
            'visual_analysis': []
        }
        
        # Find missing sections in sandbox
        for prod_section in prod_sections:
            found_match = False
            for sandbox_section in sandbox_sections:
                # Match by ID, class, or content similarity
                if (prod_section['id'] and prod_section['id'] == sandbox_section['id']) or \
                   (prod_section['className'] and prod_section['className'] == sandbox_section['className']) or \
                   (self._text_similarity(prod_section['textContent'], sandbox_section['textContent']) > 0.7):
                    found_match = True
                    break
            
            if not found_match:
                comparison['missing_sections'].append({
                    'production_section': prod_section,
                    'reason': 'Not found in sandbox',
                    'impact': 'high' if prod_section['boundingRect']['height'] > 200 else 'medium'
                })
        
        # Compare heights of matching sections
        for prod_section in prod_sections:
            for sandbox_section in sandbox_sections:
                if self._sections_match(prod_section, sandbox_section):
                    height_diff = abs(prod_section['boundingRect']['height'] - sandbox_section['boundingRect']['height'])
                    if height_diff > 20:  # Significant height difference
                        comparison['height_differences'].append({
                            'production_height': prod_section['boundingRect']['height'],
                            'sandbox_height': sandbox_section['boundingRect']['height'],
                            'difference': height_diff,
                            'section_id': prod_section.get('id', prod_section.get('className', 'unknown')),
                            'impact': 'high' if height_diff > 100 else 'medium'
                        })
        
        # Get page heights for overall comparison
        prod_height = await prod_page.evaluate('document.documentElement.scrollHeight')
        sandbox_height = await sandbox_page.evaluate('document.documentElement.scrollHeight')
        
        comparison['page_heights'] = {
            'production': prod_height,
            'sandbox': sandbox_height,
            'difference': abs(prod_height - sandbox_height),
            'percentage_diff': abs(prod_height - sandbox_height) / prod_height * 100
        }
        
        return comparison
    
    def _sections_match(self, section1, section2):
        """Determine if two sections are the same"""
        # Match by ID first
        if section1['id'] and section1['id'] == section2['id']:
            return True
            
        # Match by primary class
        if section1['className'] and section2['className']:
            class1 = section1['className'].split()[0]
            class2 = section2['className'].split()[0]
            if class1 == class2:
                return True
        
        # Match by content similarity
        return self._text_similarity(section1['textContent'], section2['textContent']) > 0.8
    
    def _text_similarity(self, text1, text2):
        """Simple text similarity measure"""
        if not text1 or not text2:
            return 0
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0
    
    def _save_comparison_results(self, results):
        """Save comparison results"""
        print(f"💾 Saving comparison results...")
        
        # Save detailed JSON
        with open(self.output_dir / "section_comparison.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        # Generate summary report
        self._generate_summary_report(results)
        
        print(f"✅ Results saved to {self.output_dir}")
    
    def _generate_summary_report(self, results):
        """Generate human-readable summary"""
        report = []
        report.append("# Section Comparison Report\n")
        
        # Page height analysis
        height_data = results['page_heights']
        report.append(f"## Page Height Analysis")
        report.append(f"- Production: {height_data['production']}px")
        report.append(f"- Sandbox: {height_data['sandbox']}px")
        report.append(f"- Difference: {height_data['difference']}px ({height_data['percentage_diff']:.1f}%)\n")
        
        # Missing sections
        if results['missing_sections']:
            report.append(f"## Missing Sections ({len(results['missing_sections'])} found)")
            for i, section in enumerate(results['missing_sections'], 1):
                report.append(f"{i}. **{section['production_section']['tag']}** "
                            f"(class: {section['production_section']['className']}) "
                            f"- Height: {section['production_section']['boundingRect']['height']}px")
                report.append(f"   Impact: {section['impact']}")
                report.append(f"   Content preview: {section['production_section']['textContent'][:100]}...\n")
        
        # Height differences
        if results['height_differences']:
            report.append(f"## Height Differences ({len(results['height_differences'])} found)")
            for i, diff in enumerate(results['height_differences'], 1):
                report.append(f"{i}. **{diff['section_id']}**: "
                            f"{diff['production_height']}px → {diff['sandbox_height']}px "
                            f"(diff: {diff['difference']}px)")
        
        # Section count summary
        meta = results['metadata']
        report.append(f"\n## Section Count Summary")
        report.append(f"- Production sections: {meta['production_sections']}")
        report.append(f"- Sandbox sections: {meta['sandbox_sections']}")
        report.append(f"- Count match: {'✅' if meta['section_count_match'] else '❌'}")
        
        # Save report
        with open(self.output_dir / "section_comparison_report.md", 'w') as f:
            f.write('\n'.join(report))

async def main():
    parser = argparse.ArgumentParser(description='Section-Level Comparison Tool v0.1.1')
    parser.add_argument('production_url', help='Production URL to compare')
    parser.add_argument('sandbox_url', help='Sandbox URL to compare')
    parser.add_argument('-o', '--output', default='section_comparison', help='Output directory')
    parser.add_argument('--auth', help='Basic auth for sandbox in format username:password')
    
    args = parser.parse_args()
    
    comparer = SectionComparer(output_dir=args.output)
    results = await comparer.compare_page_sections(
        args.production_url, 
        args.sandbox_url, 
        auth=args.auth
    )
    
    print(f"\n📊 Comparison Summary:")
    print(f"   Page height difference: {results['page_heights']['difference']}px")
    print(f"   Missing sections: {len(results['missing_sections'])}")
    print(f"   Height differences: {len(results['height_differences'])}")
    print(f"   Report saved to: {Path(args.output) / 'section_comparison_report.md'}")

if __name__ == "__main__":
    asyncio.run(main())