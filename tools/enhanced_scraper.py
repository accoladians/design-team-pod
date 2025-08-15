#!/usr/bin/env python3
"""
Enhanced Content Scraper v0.1.1 - Design Team Pod
Extracts computed styles, layout measurements, and component structure
"""

import asyncio
import json
import os
import requests
from pathlib import Path
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse
import argparse
import sys

class EnhancedScraper:
    def __init__(self, output_dir="scraped_enhanced", auth=None):
        self.output_dir = Path(output_dir)
        self.auth = auth
        self.content_data = {}
        self.computed_styles = {}
        self.layout_measurements = {}
        self.component_structure = {}
        
    async def extract_complete_page(self, url):
        """Extract everything needed for pixel-perfect cloning"""
        print(f"🕷️  Enhanced scraping: {url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            # Add HTTP auth if provided
            if self.auth:
                username, password = self.auth.split(':')
                await context.set_http_credentials(username=username, password=password)
            
            page = await context.new_page()
            
            try:
                # Navigate and wait for full load
                await page.goto(url, wait_until='networkidle', timeout=60000)
                
                # Extract all the data we need
                await self._extract_html_content(page)
                await self._extract_computed_styles(page)
                await self._extract_layout_measurements(page)
                await self._extract_component_structure(page)
                await self._extract_assets(page, url)
                
                # Take comprehensive screenshots
                await self._take_screenshots(page)
                
                print(f"✅ Enhanced extraction complete")
                return self._save_enhanced_data()
                
            finally:
                await browser.close()
    
    async def _extract_html_content(self, page):
        """Extract clean HTML content"""
        print("📄 Extracting HTML content...")
        
        # Get the full page HTML
        html_content = await page.content()
        
        # Extract text content and structure
        text_content = await page.evaluate("""
            () => {
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                const textNodes = [];
                let node;
                while (node = walker.nextNode()) {
                    if (node.textContent.trim()) {
                        textNodes.push({
                            text: node.textContent.trim(),
                            parentTag: node.parentElement?.tagName,
                            parentClass: node.parentElement?.className
                        });
                    }
                }
                return textNodes;
            }
        """)
        
        self.content_data = {
            'html': html_content,
            'text_nodes': text_content,
            'url': page.url,
            'title': await page.title()
        }
    
    async def _extract_computed_styles(self, page):
        """Extract computed CSS styles for all elements"""
        print("🎨 Extracting computed styles...")
        
        computed_styles = await page.evaluate("""
            () => {
                const elements = document.querySelectorAll('*');
                const styles = {};
                
                elements.forEach((el, index) => {
                    if (el.getBoundingClientRect().width > 0 || el.getBoundingClientRect().height > 0) {
                        const computedStyle = window.getComputedStyle(el);
                        const selector = el.tagName + (el.className ? '.' + el.className.split(' ').join('.') : '') + (el.id ? '#' + el.id : '');
                        
                        styles[`element_${index}`] = {
                            selector: selector,
                            tag: el.tagName,
                            className: el.className,
                            id: el.id,
                            styles: {
                                // Layout
                                display: computedStyle.display,
                                position: computedStyle.position,
                                top: computedStyle.top,
                                left: computedStyle.left,
                                width: computedStyle.width,
                                height: computedStyle.height,
                                // Box model
                                margin: computedStyle.margin,
                                marginTop: computedStyle.marginTop,
                                marginRight: computedStyle.marginRight,
                                marginBottom: computedStyle.marginBottom,
                                marginLeft: computedStyle.marginLeft,
                                padding: computedStyle.padding,
                                paddingTop: computedStyle.paddingTop,
                                paddingRight: computedStyle.paddingRight,
                                paddingBottom: computedStyle.paddingBottom,
                                paddingLeft: computedStyle.paddingLeft,
                                border: computedStyle.border,
                                borderRadius: computedStyle.borderRadius,
                                // Typography
                                fontFamily: computedStyle.fontFamily,
                                fontSize: computedStyle.fontSize,
                                fontWeight: computedStyle.fontWeight,
                                lineHeight: computedStyle.lineHeight,
                                letterSpacing: computedStyle.letterSpacing,
                                textAlign: computedStyle.textAlign,
                                color: computedStyle.color,
                                // Background
                                backgroundColor: computedStyle.backgroundColor,
                                backgroundImage: computedStyle.backgroundImage,
                                backgroundSize: computedStyle.backgroundSize,
                                backgroundPosition: computedStyle.backgroundPosition,
                                // Flexbox/Grid
                                flexDirection: computedStyle.flexDirection,
                                justifyContent: computedStyle.justifyContent,
                                alignItems: computedStyle.alignItems,
                                gap: computedStyle.gap,
                                gridTemplateColumns: computedStyle.gridTemplateColumns,
                                gridTemplateRows: computedStyle.gridTemplateRows
                            }
                        };
                    }
                });
                
                return styles;
            }
        """)
        
        self.computed_styles = computed_styles
    
    async def _extract_layout_measurements(self, page):
        """Extract precise layout measurements"""
        print("📏 Extracting layout measurements...")
        
        measurements = await page.evaluate("""
            () => {
                const elements = document.querySelectorAll('*');
                const measurements = {};
                
                elements.forEach((el, index) => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 || rect.height > 0) {
                        measurements[`element_${index}`] = {
                            tag: el.tagName,
                            className: el.className,
                            boundingRect: {
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height,
                                top: rect.top,
                                right: rect.right,
                                bottom: rect.bottom,
                                left: rect.left
                            },
                            scrollDimensions: {
                                scrollWidth: el.scrollWidth,
                                scrollHeight: el.scrollHeight,
                                scrollTop: el.scrollTop,
                                scrollLeft: el.scrollLeft
                            },
                            offsetDimensions: {
                                offsetWidth: el.offsetWidth,
                                offsetHeight: el.offsetHeight,
                                offsetTop: el.offsetTop,
                                offsetLeft: el.offsetLeft
                            }
                        };
                    }
                });
                
                return measurements;
            }
        """)
        
        self.layout_measurements = measurements
    
    async def _extract_component_structure(self, page):
        """Identify page components and sections"""
        print("🧩 Extracting component structure...")
        
        components = await page.evaluate("""
            () => {
                const sections = [];
                
                // Find major sections
                const sectionElements = document.querySelectorAll('section, article, main, header, footer, nav, aside, .section, .container, [class*="section"]');
                
                sectionElements.forEach((el, index) => {
                    const rect = el.getBoundingClientRect();
                    if (rect.height > 50) { // Ignore tiny sections
                        sections.push({
                            index: index,
                            tag: el.tagName,
                            className: el.className,
                            id: el.id,
                            boundingRect: {
                                x: rect.x,
                                y: rect.y,
                                width: rect.width,
                                height: rect.height
                            },
                            innerHTML: el.innerHTML.substring(0, 500), // First 500 chars for analysis
                            childCount: el.children.length,
                            textContent: el.textContent?.substring(0, 200) || ''
                        });
                    }
                });
                
                return {
                    sections: sections,
                    totalSections: sections.length,
                    pageHeight: document.documentElement.scrollHeight,
                    viewportHeight: window.innerHeight
                };
            }
        """)
        
        self.component_structure = components
    
    async def _extract_assets(self, page, base_url):
        """Extract and download assets"""
        print("🖼️  Extracting assets...")
        
        # Create assets directory
        assets_dir = self.output_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Get all images
        images = await page.evaluate("""
            () => {
                const images = Array.from(document.querySelectorAll('img'));
                return images.map(img => ({
                    src: img.src,
                    alt: img.alt,
                    width: img.naturalWidth,
                    height: img.naturalHeight,
                    className: img.className
                }));
            }
        """)
        
        # Download images
        downloaded_assets = []
        for img in images:
            if img['src']:
                try:
                    img_url = urljoin(base_url, img['src'])
                    filename = os.path.basename(urlparse(img_url).path) or 'image.jpg'
                    filepath = assets_dir / filename
                    
                    response = requests.get(img_url, timeout=10)
                    if response.status_code == 200:
                        with open(filepath, 'wb') as f:
                            f.write(response.content)
                        downloaded_assets.append({
                            'original_url': img_url,
                            'local_path': str(filepath),
                            'info': img
                        })
                except Exception as e:
                    print(f"Failed to download {img['src']}: {e}")
        
        self.assets = downloaded_assets
    
    async def _take_screenshots(self, page):
        """Take comprehensive screenshots"""
        print("📸 Taking screenshots...")
        
        screenshots_dir = self.output_dir / "screenshots"
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Full page screenshot
        await page.screenshot(
            path=screenshots_dir / "fullpage.png",
            full_page=True
        )
        
        # Viewport screenshot
        await page.screenshot(
            path=screenshots_dir / "viewport.png",
            full_page=False
        )
        
        # Take section screenshots
        sections = self.component_structure.get('sections', [])
        for i, section in enumerate(sections[:10]):  # Limit to first 10 sections
            try:
                # Find element and screenshot it
                element = await page.query_selector(f'.{section["className"].split()[0]}' if section["className"] else section["tag"])
                if element:
                    await element.screenshot(path=screenshots_dir / f"section_{i}.png")
            except:
                continue
    
    def _save_enhanced_data(self):
        """Save all extracted data"""
        print("💾 Saving enhanced data...")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save comprehensive data
        enhanced_data = {
            'metadata': {
                'scraper_version': '0.1.1',
                'timestamp': 'current',
                'url': self.content_data.get('url', ''),
                'total_sections': self.component_structure.get('totalSections', 0),
                'page_height': self.component_structure.get('pageHeight', 0)
            },
            'content': self.content_data,
            'computed_styles': self.computed_styles,
            'layout_measurements': self.layout_measurements,
            'component_structure': self.component_structure,
            'assets': getattr(self, 'assets', [])
        }
        
        # Save to JSON
        with open(self.output_dir / "enhanced_extraction.json", 'w') as f:
            json.dump(enhanced_data, f, indent=2)
        
        # Save individual components for easier analysis
        with open(self.output_dir / "computed_styles.json", 'w') as f:
            json.dump(self.computed_styles, f, indent=2)
            
        with open(self.output_dir / "layout_measurements.json", 'w') as f:
            json.dump(self.layout_measurements, f, indent=2)
            
        with open(self.output_dir / "component_structure.json", 'w') as f:
            json.dump(self.component_structure, f, indent=2)
        
        print(f"✅ Enhanced data saved to {self.output_dir}")
        return enhanced_data

async def main():
    parser = argparse.ArgumentParser(description='Enhanced Content Scraper v0.1.1')
    parser.add_argument('url', help='URL to scrape')
    parser.add_argument('-o', '--output', default='scraped_enhanced', help='Output directory')
    parser.add_argument('--auth', help='Basic auth in format username:password')
    
    args = parser.parse_args()
    
    scraper = EnhancedScraper(output_dir=args.output, auth=args.auth)
    result = await scraper.extract_complete_page(args.url)
    
    print(f"\n📊 Extraction Summary:")
    print(f"   Total sections found: {result['metadata']['total_sections']}")
    print(f"   Page height: {result['metadata']['page_height']}px")
    print(f"   Elements with styles: {len(result['computed_styles'])}")
    print(f"   Assets downloaded: {len(result['assets'])}")

if __name__ == "__main__":
    asyncio.run(main())