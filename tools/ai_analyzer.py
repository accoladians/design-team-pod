#!/usr/bin/env python3
"""
AI Analyzer for Design Team Pod
Integrates with multiple AI providers for visual analysis and recommendations
"""

import os
import sys
import json
import base64
import asyncio
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Union
import logging

try:
    import openai
    import anthropic
    # import google.generativeai as genai  # Commented out for now
    from rich.console import Console
    from rich.progress import Progress
    import structlog
except ImportError:
    print("Missing dependencies. Install with: pip install -r requirements.txt")
    sys.exit(1)

# Setup structured logging
logger = structlog.get_logger()
console = Console()

class AIAnalyzer:
    """AI-powered visual analysis coordinator"""
    
    def __init__(self, workspace_dir: str = "/app/workspace"):
        self.workspace = Path(workspace_dir)
        self.results_dir = self.workspace / "output" / f"ai_analysis_{int(time.time())}"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize AI clients
        self.clients = {}
        self._init_ai_clients()
        
        # Analysis results
        self.results = {
            'metadata': {
                'timestamp': time.time(),
                'version': '2.0.0',
                'workspace': str(self.workspace)
            },
            'analyses': {},
            'comparisons': {},
            'recommendations': {},
            'summary': {}
        }
    
    def _init_ai_clients(self):
        """Initialize AI service clients"""
        try:
            # OpenAI client
            if os.getenv('OPENAI_API_KEY'):
                self.clients['openai'] = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                logger.info("OpenAI client initialized")
            
            # Anthropic client
            if os.getenv('ANTHROPIC_API_KEY'):
                self.clients['anthropic'] = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
                logger.info("Anthropic client initialized")
            
            # Google Gemini client (placeholder - implement when available)
            # if os.getenv('GOOGLE_API_KEY'):
            #     genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            #     self.clients['gemini'] = genai
            #     logger.info("Gemini client initialized")
            
        except Exception as e:
            logger.error("AI client initialization failed", error=str(e))
    
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64 for API calls"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error("Image encoding failed", path=image_path, error=str(e))
            return None
    
    async def analyze_with_openai(self, image_path: str, prompt: str = None) -> Dict:
        """Analyze image with OpenAI GPT-4V"""
        if 'openai' not in self.clients:
            return {'success': False, 'error': 'OpenAI client not available'}
        
        try:
            # Default analysis prompt
            if not prompt:
                prompt = """Analyze this webpage screenshot for design and UX quality. Provide:
                1. Overall design assessment (modern, clean, professional, etc.)
                2. Layout structure analysis (grid, spacing, alignment)
                3. Typography evaluation (readability, hierarchy, consistency)
                4. Color scheme assessment (harmony, contrast, accessibility)
                5. Visual hierarchy effectiveness
                6. Mobile responsiveness indicators
                7. Potential UX issues or improvements
                8. Overall quality score (1-10) with reasoning
                
                Format as structured JSON with clear categories."""
            
            base64_image = self.encode_image(image_path)
            if not base64_image:
                return {'success': False, 'error': 'Failed to encode image'}
            
            response = await asyncio.to_thread(
                self.clients['openai'].chat.completions.create,
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1500,
                temperature=0.1
            )
            
            analysis_text = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to text
            try:
                analysis = json.loads(analysis_text)
            except json.JSONDecodeError:
                analysis = {'raw_analysis': analysis_text}
            
            return {
                'success': True,
                'provider': 'openai',
                'model': 'gpt-4-vision-preview',
                'analysis': analysis,
                'usage': response.usage._asdict() if response.usage else None
            }
            
        except Exception as e:
            logger.error("OpenAI analysis failed", error=str(e))
            return {'success': False, 'error': str(e), 'provider': 'openai'}
    
    async def analyze_with_anthropic(self, image_path: str, prompt: str = None) -> Dict:
        """Analyze image with Anthropic Claude"""
        if 'anthropic' not in self.clients:
            return {'success': False, 'error': 'Anthropic client not available'}
        
        try:
            # Default analysis prompt
            if not prompt:
                prompt = """Analyze this webpage screenshot comprehensively. Focus on:

                DESIGN QUALITY:
                - Visual hierarchy and information architecture
                - Typography choices and readability
                - Color harmony and brand consistency
                - Spacing, alignment, and grid usage
                
                USER EXPERIENCE:
                - Navigation clarity and accessibility
                - Content organization and flow
                - Call-to-action effectiveness
                - Mobile/responsive design indicators
                
                TECHNICAL ASSESSMENT:
                - Loading performance indicators
                - Accessibility considerations
                - Modern web standards compliance
                
                RECOMMENDATIONS:
                - Specific improvements for better UX
                - Design enhancements for visual appeal
                - Accessibility improvements
                
                Provide a quality score (1-100) and detailed reasoning."""
            
            base64_image = self.encode_image(image_path)
            if not base64_image:
                return {'success': False, 'error': 'Failed to encode image'}
            
            response = await asyncio.to_thread(
                self.clients['anthropic'].messages.create,
                model="claude-3-sonnet-20240229",
                max_tokens=1500,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": base64_image
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            analysis_text = response.content[0].text
            
            # Try to extract structured data from response
            try:
                # Look for JSON in the response
                if '{' in analysis_text and '}' in analysis_text:
                    start = analysis_text.find('{')
                    end = analysis_text.rfind('}') + 1
                    json_text = analysis_text[start:end]
                    analysis = json.loads(json_text)
                else:
                    analysis = {'raw_analysis': analysis_text}
            except (json.JSONDecodeError, ValueError):
                analysis = {'raw_analysis': analysis_text}
            
            return {
                'success': True,
                'provider': 'anthropic',
                'model': 'claude-3-sonnet-20240229',
                'analysis': analysis,
                'usage': response.usage._asdict() if hasattr(response, 'usage') else None
            }
            
        except Exception as e:
            logger.error("Anthropic analysis failed", error=str(e))
            return {'success': False, 'error': str(e), 'provider': 'anthropic'}
    
    async def compare_images(self, image1_path: str, image2_path: str, provider: str = 'anthropic') -> Dict:
        """Compare two images using AI vision"""
        try:
            comparison_prompt = """Compare these two webpage screenshots and provide:
            
            VISUAL DIFFERENCES:
            - Layout changes and positioning differences
            - Typography variations (fonts, sizes, spacing)
            - Color differences and brand consistency
            - Image and asset variations
            
            QUALITY COMPARISON:
            - Which version has better visual hierarchy
            - User experience improvements or regressions
            - Accessibility considerations
            - Overall design quality assessment
            
            PIXEL-PERFECT ASSESSMENT:
            - Accuracy level (percentage estimate)
            - Most significant discrepancies
            - Areas needing attention for exact matching
            
            RECOMMENDATIONS:
            - Priority fixes for pixel-perfect accuracy
            - Design improvements regardless of accuracy
            - Technical implementation suggestions
            
            Provide an overall accuracy score (0-100) and specific action items."""
            
            if provider == 'anthropic' and 'anthropic' in self.clients:
                # Create side-by-side comparison for Anthropic
                from PIL import Image
                
                img1 = Image.open(image1_path)
                img2 = Image.open(image2_path)
                
                # Resize to same height if needed
                if img1.height != img2.height:
                    min_height = min(img1.height, img2.height)
                    img1 = img1.resize((int(img1.width * min_height / img1.height), min_height))
                    img2 = img2.resize((int(img2.width * min_height / img2.height), min_height))
                
                # Create side-by-side comparison
                combined_width = img1.width + img2.width
                combined = Image.new('RGB', (combined_width, img1.height), 'white')
                combined.paste(img1, (0, 0))
                combined.paste(img2, (img1.width, 0))
                
                # Save comparison image
                comparison_path = self.results_dir / "comparison_combined.png"
                combined.save(comparison_path)
                
                # Analyze combined image
                result = await self.analyze_with_anthropic(str(comparison_path), comparison_prompt)
                
            elif provider == 'openai' and 'openai' in self.clients:
                # For OpenAI, we'll analyze each image separately then compare
                analysis1 = await self.analyze_with_openai(image1_path, "Analyze this webpage design in detail.")
                analysis2 = await self.analyze_with_openai(image2_path, "Analyze this webpage design in detail.")
                
                # Combine analyses
                result = {
                    'success': True,
                    'provider': 'openai',
                    'comparison_type': 'separate_analysis',
                    'image1_analysis': analysis1,
                    'image2_analysis': analysis2,
                    'comparison_summary': 'Combined analysis from separate evaluations'
                }
            else:
                return {'success': False, 'error': f'Provider {provider} not available'}
            
            return result
            
        except Exception as e:
            logger.error("Image comparison failed", error=str(e))
            return {'success': False, 'error': str(e), 'provider': provider}
    
    async def run_comprehensive_analysis(self, image_path: str, comparison_image: str = None) -> Dict:
        """Run comprehensive AI analysis on image(s)"""
        console.print(f"[bold green]Starting comprehensive AI analysis...[/bold green]")
        
        available_providers = list(self.clients.keys())
        if not available_providers:
            console.print("[red]No AI providers available. Check API keys.[/red]")
            return {'success': False, 'error': 'No AI providers configured'}
        
        with Progress() as progress:
            task = progress.add_task("[cyan]Running AI analyses...", total=len(available_providers))
            
            # Single image analysis with all providers
            for provider in available_providers:
                console.print(f"[yellow]Analyzing with {provider}...[/yellow]")
                
                if provider == 'openai':
                    result = await self.analyze_with_openai(image_path)
                elif provider == 'anthropic':
                    result = await self.analyze_with_anthropic(image_path)
                # elif provider == 'gemini':
                #     result = await self.analyze_with_gemini(image_path)
                
                self.results['analyses'][provider] = result
                progress.advance(task)
            
            # Image comparison if second image provided
            if comparison_image:
                console.print("[yellow]Running image comparison...[/yellow]")
                comparison_result = await self.compare_images(image_path, comparison_image)
                self.results['comparisons']['primary'] = comparison_result
        
        # Generate summary and recommendations
        self._generate_summary()
        
        # Save results
        results_path = self.results_dir / "ai_analysis_results.json"
        with open(results_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        console.print(f"[bold green]AI analysis complete! Results saved to: {results_path}[/bold green]")
        
        return self.results
    
    def _generate_summary(self):
        """Generate summary from all AI analyses"""
        successful_analyses = [
            result for result in self.results['analyses'].values() 
            if result.get('success')
        ]
        
        if not successful_analyses:
            self.results['summary'] = {'error': 'No successful analyses'}
            return
        
        # Aggregate recommendations
        all_recommendations = []
        quality_scores = []
        
        for analysis in successful_analyses:
            if isinstance(analysis.get('analysis'), dict):
                # Extract recommendations and scores
                raw_analysis = analysis['analysis'].get('raw_analysis', '')
                if 'recommendation' in raw_analysis.lower():
                    all_recommendations.append(raw_analysis)
                
                # Try to extract numeric scores
                import re
                scores = re.findall(r'(?:score|rating|quality)[:\s]*(\d+)', raw_analysis.lower())
                for score in scores:
                    try:
                        quality_scores.append(int(score))
                    except ValueError:
                        continue
        
        # Calculate average quality score
        avg_score = sum(quality_scores) / len(quality_scores) if quality_scores else None
        
        self.results['summary'] = {
            'total_analyses': len(successful_analyses),
            'average_quality_score': avg_score,
            'providers_used': [analysis.get('provider') for analysis in successful_analyses],
            'has_comparison': bool(self.results.get('comparisons')),
            'recommendations_count': len(all_recommendations)
        }

def main():
    parser = argparse.ArgumentParser(description="AI Analyzer for Design Team")
    parser.add_argument("image", help="Primary image to analyze")
    parser.add_argument("--compare", help="Second image for comparison")
    parser.add_argument("--provider", choices=["openai", "anthropic", "all"], default="all", 
                       help="AI provider to use")
    parser.add_argument("--prompt", help="Custom analysis prompt")
    parser.add_argument("--workspace", default="/app/workspace", help="Workspace directory")
    parser.add_argument("--output-format", default="json", choices=["json", "text"], 
                       help="Output format")
    
    args = parser.parse_args()
    
    # Validate input
    if not Path(args.image).exists():
        console.print(f"[red]Error: {args.image} not found[/red]")
        sys.exit(1)
    
    if args.compare and not Path(args.compare).exists():
        console.print(f"[red]Error: {args.compare} not found[/red]")
        sys.exit(1)
    
    # Run analysis
    analyzer = AIAnalyzer(args.workspace)
    
    try:
        if args.provider == "all":
            results = asyncio.run(analyzer.run_comprehensive_analysis(args.image, args.compare))
        else:
            # Single provider analysis
            if args.provider == "openai":
                results = asyncio.run(analyzer.analyze_with_openai(args.image, args.prompt))
            elif args.provider == "anthropic":
                results = asyncio.run(analyzer.analyze_with_anthropic(args.image, args.prompt))
            
            if args.compare:
                comparison = asyncio.run(analyzer.compare_images(args.image, args.compare, args.provider))
                results['comparison'] = comparison
        
        if args.output_format == "json":
            print(json.dumps(results, indent=2))
        else:
            console.print(f"\n[bold]AI Analysis Results[/bold]")
            if 'summary' in results:
                summary = results['summary']
                console.print(f"Analyses: {summary.get('total_analyses', 0)}")
                if summary.get('average_quality_score'):
                    console.print(f"Average Quality Score: {summary['average_quality_score']:.1f}")
                console.print(f"Providers: {', '.join(summary.get('providers_used', []))}")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        logger.exception("AI analysis failed")
        sys.exit(1)

if __name__ == "__main__":
    import time
    main()