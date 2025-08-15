#!/usr/bin/env python3
"""
Content Scraper for Visual Diff Toolkit
Scrapes ALL content and images from production websites for pixel-perfect cloning
"""

import os
import sys
import json
import requests
import hashlib
from urllib.parse import urljoin, urlparse, unquote
from pathlib import Path
import time
from typing import Dict, List, Optional, Tuple
import argparse

try:
    from bs4 import BeautifulSoup
    from PIL import Image
except ImportError:
    print("Missing dependencies. Install with:")
    print("pip3 install beautifulsoup4 lxml Pillow requests")
    sys.exit(1)

class ContentScraper:
    def __init__(self, base_url: str, output_dir: str, auth: Optional[Tuple[str, str]] = None):
        self.base_url = base_url.rstrip('/')
        self.domain = urlparse(base_url).netloc
        self.output_dir = Path(output_dir)
        self.auth = auth
        self.session = requests.Session()
        
        if auth:
            self.session.auth = auth
            
        # Create directory structure
        self.content_dir = self.output_dir / "content"
        self.images_dir = self.output_dir / "images"
        self.styles_dir = self.output_dir / "styles"
        self.scripts_dir = self.output_dir / "scripts"
        self.data_dir = self.output_dir / "data"
        
        for directory in [self.content_dir, self.images_dir, self.styles_dir, self.scripts_dir, self.data_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
        self.scraped_urls = set()
        self.scraped_assets = set()
        
    def get_file_hash(self, content: bytes) -> str:
        """Generate SHA256 hash for content deduplication"""
        return hashlib.sha256(content).hexdigest()[:16]
    
    def sanitize_filename(self, url: str) -> str:
        """Convert URL to safe filename"""
        parsed = urlparse(url)
        path = parsed.path or '/'
        
        # Remove leading slash and replace special chars
        filename = path.lstrip('/').replace('/', '_').replace('\\', '_')
        if parsed.query:
            filename += f"__{parsed.query.replace('&', '_').replace('=', '-')}"
            
        # Limit length and add extension if missing
        filename = filename[:100]
        if not filename:
            filename = "index"
            
        return filename
    
    def download_asset(self, url: str, asset_type: str = "unknown") -> Optional[str]:
        """Download and save asset, return local path"""
        try:
            # Make URL absolute
            if url.startswith('//'):
                url = 'https:' + url
            elif url.startswith('/'):
                url = urljoin(self.base_url, url)
            elif not url.startswith(('http://', 'https://')):
                url = urljoin(self.base_url, url)
                
            if url in self.scraped_assets:
                return None
                
            self.scraped_assets.add(url)
            
            print(f"📥 Downloading {asset_type}: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Determine file extension from content-type or URL
            content_type = response.headers.get('content-type', '').lower()
            url_path = urlparse(url).path.lower()
            
            if 'image/' in content_type or url_path.endswith(('.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp')):
                save_dir = self.images_dir
                if url_path.endswith('.svg'):
                    ext = '.svg'
                elif 'jpeg' in content_type or url_path.endswith(('.jpg', '.jpeg')):
                    ext = '.jpg'
                elif 'png' in content_type or url_path.endswith('.png'):
                    ext = '.png'
                elif 'gif' in content_type or url_path.endswith('.gif'):
                    ext = '.gif'
                elif 'webp' in content_type or url_path.endswith('.webp'):
                    ext = '.webp'
                else:
                    ext = '.img'
            elif 'css' in content_type or url_path.endswith('.css'):
                save_dir = self.styles_dir
                ext = '.css'
            elif 'javascript' in content_type or url_path.endswith('.js'):
                save_dir = self.scripts_dir
                ext = '.js'
            else:
                save_dir = self.data_dir
                ext = '.bin'
                
            # Generate filename
            base_name = self.sanitize_filename(url)
            file_hash = self.get_file_hash(response.content)
            filename = f"{base_name}_{file_hash}{ext}"
            
            file_path = save_dir / filename
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(response.content)
                
            # Save metadata
            metadata = {
                'original_url': url,
                'content_type': content_type,
                'size': len(response.content),
                'hash': file_hash,
                'local_path': str(file_path.relative_to(self.output_dir))
            }
            
            metadata_path = file_path.with_suffix(f"{ext}.meta.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
                
            return str(file_path.relative_to(self.output_dir))
            
        except Exception as e:
            print(f"❌ Failed to download {url}: {e}")
            return None
    
    def extract_text_content(self, soup: BeautifulSoup) -> Dict:
        """Extract all text content with structure preservation"""
        content = {
            'title': soup.title.string if soup.title else '',
            'meta_description': '',
            'headings': {},
            'paragraphs': [],
            'links': [],
            'images': [],
            'forms': [],
            'lists': [],
            'tables': []
        }
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            content['meta_description'] = meta_desc.get('content', '')
            
        # Headings (h1-h6)
        for level in range(1, 7):
            headings = soup.find_all(f'h{level}')
            content['headings'][f'h{level}'] = [h.get_text().strip() for h in headings]
            
        # Paragraphs
        paragraphs = soup.find_all('p')
        content['paragraphs'] = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
        
        # Links
        links = soup.find_all('a', href=True)
        for link in links:
            content['links'].append({
                'text': link.get_text().strip(),
                'href': link['href'],
                'title': link.get('title', '')
            })
            
        # Images
        images = soup.find_all('img', src=True)
        for img in images:
            content['images'].append({
                'src': img['src'],
                'alt': img.get('alt', ''),
                'title': img.get('title', ''),
                'width': img.get('width', ''),
                'height': img.get('height', '')
            })
            
        # Forms
        forms = soup.find_all('form')
        for form in forms:
            form_data = {
                'action': form.get('action', ''),
                'method': form.get('method', 'get'),
                'inputs': []
            }
            
            inputs = form.find_all(['input', 'textarea', 'select'])
            for inp in inputs:
                form_data['inputs'].append({
                    'type': inp.get('type', inp.name),
                    'name': inp.get('name', ''),
                    'placeholder': inp.get('placeholder', ''),
                    'value': inp.get('value', '')
                })
            content['forms'].append(form_data)
            
        # Lists
        for list_type in ['ul', 'ol']:
            lists = soup.find_all(list_type)
            for lst in lists:
                items = [li.get_text().strip() for li in lst.find_all('li')]
                content['lists'].append({
                    'type': list_type,
                    'items': items
                })
                
        # Tables
        tables = soup.find_all('table')
        for table in tables:
            table_data = []
            rows = table.find_all('tr')
            for row in rows:
                cells = [cell.get_text().strip() for cell in row.find_all(['td', 'th'])]
                if cells:
                    table_data.append(cells)
            if table_data:
                content['tables'].append(table_data)
                
        return content
    
    def extract_styles_and_scripts(self, soup: BeautifulSoup) -> Dict:
        """Extract all CSS and JavaScript references"""
        assets = {
            'stylesheets': [],
            'scripts': [],
            'inline_styles': [],
            'inline_scripts': []
        }
        
        # External stylesheets
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                local_path = self.download_asset(href, 'stylesheet')
                assets['stylesheets'].append({
                    'href': href,
                    'local_path': local_path,
                    'media': link.get('media', 'all')
                })
                
        # External scripts
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                local_path = self.download_asset(src, 'script')
                assets['scripts'].append({
                    'src': src,
                    'local_path': local_path,
                    'type': script.get('type', 'text/javascript')
                })
                
        # Inline styles
        for style in soup.find_all('style'):
            if style.string:
                assets['inline_styles'].append(style.string.strip())
                
        # Inline scripts
        for script in soup.find_all('script'):
            if script.string and not script.get('src'):
                assets['inline_scripts'].append(script.string.strip())
                
        return assets
    
    def scrape_page(self, url: str) -> Dict:
        """Scrape a single page comprehensively"""
        try:
            if url in self.scraped_urls:
                return {'status': 'already_scraped'}
                
            self.scraped_urls.add(url)
            
            print(f"🔍 Scraping: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract all content
            text_content = self.extract_text_content(soup)
            assets = self.extract_styles_and_scripts(soup)
            
            # Download all images
            for img_info in text_content['images']:
                img_info['local_path'] = self.download_asset(img_info['src'], 'image')
                
            # Save full HTML
            html_filename = self.sanitize_filename(url) + '.html'
            html_path = self.content_dir / html_filename
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(str(soup))
                
            page_data = {
                'url': url,
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'html_file': str(html_path.relative_to(self.output_dir)),
                'text_content': text_content,
                'assets': assets,
                'scraped_at': time.time()
            }
            
            # Save page data
            data_filename = self.sanitize_filename(url) + '.json'
            data_path = self.data_dir / data_filename
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(page_data, f, indent=2, ensure_ascii=False)
                
            return page_data
            
        except Exception as e:
            print(f"❌ Failed to scrape {url}: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def discover_pages(self, start_url: str, max_depth: int = 2) -> List[str]:
        """Discover pages by following internal links"""
        discovered = set([start_url])
        to_crawl = [(start_url, 0)]
        
        while to_crawl:
            current_url, depth = to_crawl.pop(0)
            
            if depth >= max_depth:
                continue
                
            try:
                response = self.session.get(current_url, timeout=30)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find internal links
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    
                    # Make absolute
                    if href.startswith('/'):
                        href = urljoin(self.base_url, href)
                    elif not href.startswith(('http://', 'https://')):
                        href = urljoin(current_url, href)
                        
                    # Check if internal
                    if urlparse(href).netloc == self.domain:
                        # Remove fragments and clean
                        href = href.split('#')[0]
                        
                        if href not in discovered and not href.endswith(('.pdf', '.zip', '.doc', '.xls')):
                            discovered.add(href)
                            to_crawl.append((href, depth + 1))
                            
            except Exception as e:
                print(f"⚠️ Failed to discover from {current_url}: {e}")
                
        return list(discovered)
    
    def generate_report(self) -> Dict:
        """Generate comprehensive scraping report"""
        report = {
            'base_url': self.base_url,
            'output_directory': str(self.output_dir),
            'total_pages': len(self.scraped_urls),
            'total_assets': len(self.scraped_assets),
            'scraped_at': time.time(),
            'directories': {
                'content': str(self.content_dir.relative_to(self.output_dir)),
                'images': str(self.images_dir.relative_to(self.output_dir)),
                'styles': str(self.styles_dir.relative_to(self.output_dir)),
                'scripts': str(self.scripts_dir.relative_to(self.output_dir)),
                'data': str(self.data_dir.relative_to(self.output_dir))
            }
        }
        
        # Count files by type
        for directory, name in [(self.images_dir, 'images'), (self.styles_dir, 'styles'), 
                               (self.scripts_dir, 'scripts'), (self.content_dir, 'content')]:
            files = list(directory.glob('*'))
            non_meta_files = [f for f in files if not f.name.endswith('.meta.json')]
            report[f'{name}_count'] = len(non_meta_files)
            
        return report

def main():
    parser = argparse.ArgumentParser(description='Comprehensive website content scraper')
    parser.add_argument('url', help='Base URL to scrape')
    parser.add_argument('-o', '--output', required=True, help='Output directory')
    parser.add_argument('-u', '--username', help='HTTP Basic Auth username')
    parser.add_argument('-p', '--password', help='HTTP Basic Auth password')
    parser.add_argument('-d', '--depth', type=int, default=2, help='Maximum crawl depth (default: 2)')
    parser.add_argument('--single-page', action='store_true', help='Scrape only the specified URL')
    
    args = parser.parse_args()
    
    # Setup authentication
    auth = None
    if args.username and args.password:
        auth = (args.username, args.password)
        
    # Initialize scraper
    scraper = ContentScraper(args.url, args.output, auth)
    
    try:
        if args.single_page:
            # Scrape only the specified page
            pages = [args.url]
        else:
            # Discover pages
            print(f"🔍 Discovering pages from {args.url} (depth: {args.depth})...")
            pages = scraper.discover_pages(args.url, args.depth)
            print(f"📄 Found {len(pages)} pages to scrape")
            
        # Scrape all pages
        for i, page_url in enumerate(pages, 1):
            print(f"[{i}/{len(pages)}] Scraping: {page_url}")
            scraper.scrape_page(page_url)
            time.sleep(0.5)  # Be nice to the server
            
        # Generate report
        report = scraper.generate_report()
        report_path = scraper.output_dir / 'scraping_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n🎉 Scraping complete!")
        print(f"📊 Report saved to: {report_path}")
        print(f"📄 Scraped {report['total_pages']} pages")
        print(f"🖼️ Downloaded {report['images_count']} images")
        print(f"🎨 Downloaded {report['styles_count']} stylesheets")
        print(f"⚙️ Downloaded {report['scripts_count']} scripts")
        
    except KeyboardInterrupt:
        print("\n⚠️ Scraping interrupted by user")
    except Exception as e:
        print(f"💥 Scraping failed: {e}")
        return 1
        
    return 0

if __name__ == '__main__':
    sys.exit(main())