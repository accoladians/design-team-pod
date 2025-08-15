#!/usr/bin/env python3
"""
Comprehensive Visual Diff Toolkit
Coordinates multiple visual comparison methods and AI analysis for pixel-perfect website cloning
"""

import os
import sys
import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import argparse
import hashlib
from urllib.parse import urlparse

try:
    import requests
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
except ImportError:
    print("Missing dependencies. Install with:")
    print("pip3 install Pillow requests numpy")
    sys.exit(1)

class VisualDiffAnalyzer:
    """Main coordinator for visual diff analysis using multiple tools and AI"""
    
    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path("visual_diff_results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Tool availability
        self.available_tools = self._check_tool_availability()
        
        # Results storage
        self.results = {
            'metadata': {},
            'tool_results': {},
            'ai_analysis': {},
            'summary': {}
        }
        
    def _check_tool_availability(self) -> Dict[str, bool]:
        """Check which visual diff tools are available"""
        tools = {
            'imagemagick': self._check_command('magick') or self._check_command('compare'),
            'perceptualdiff': self._check_command('perceptualdiff'),
            'dssim': self._check_command('dssim'),
            'butteraugli': self._check_command('butteraugli'),
            'vips': self._check_command('vips')
        }
        
        print("🔧 Tool Availability:")
        for tool, available in tools.items():
            status = "✅" if available else "❌"
            print(f"  {status} {tool}")
            
        return tools
    
    def _check_command(self, command: str) -> bool:
        """Check if a command is available in PATH"""
        try:
            subprocess.run([command, '--version'], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL, 
                         check=False)
            return True
        except FileNotFoundError:
            return False
    
    def _ensure_image_format(self, image_path: str) -> str:
        """Ensure image is in a format compatible with all tools"""
        img_path = Path(image_path)
        
        # Convert to PNG if needed (most compatible format)
        if img_path.suffix.lower() not in ['.png', '.jpg', '.jpeg']:
            try:
                with Image.open(img_path) as img:
                    # Convert to RGB if needed
                    if img.mode in ('RGBA', 'LA', 'P'):
                        img = img.convert('RGB')
                    
                    png_path = img_path.with_suffix('.png')
                    img.save(png_path, 'PNG')
                    return str(png_path)
            except Exception as e:
                print(f"⚠️ Failed to convert {img_path}: {e}")
                return str(img_path)
        
        return str(img_path)
    
    def _normalize_images(self, img1_path: str, img2_path: str) -> Tuple[str, str]:
        """Normalize images to same size for comparison"""
        try:
            with Image.open(img1_path) as img1, Image.open(img2_path) as img2:
                # Get dimensions
                w1, h1 = img1.size
                w2, h2 = img2.size
                
                # If same size, no normalization needed
                if (w1, h1) == (w2, h2):
                    return img1_path, img2_path
                
                # Resize to smaller dimensions to avoid upscaling
                target_width = min(w1, w2)
                target_height = min(h1, h2)
                
                # Create normalized versions
                norm1_path = self.output_dir / f"norm1_{int(time.time())}.png"
                norm2_path = self.output_dir / f"norm2_{int(time.time())}.png"
                
                # Resize images
                img1_resized = img1.resize((target_width, target_height), Image.Resampling.LANCZOS)
                img2_resized = img2.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                # Convert to RGB if needed
                if img1_resized.mode != 'RGB':
                    img1_resized = img1_resized.convert('RGB')
                if img2_resized.mode != 'RGB':
                    img2_resized = img2_resized.convert('RGB')
                
                # Save normalized images
                img1_resized.save(norm1_path)
                img2_resized.save(norm2_path)
                
                print(f"📏 Normalized images to {target_width}x{target_height}")
                return str(norm1_path), str(norm2_path)
                
        except Exception as e:
            print(f"⚠️ Failed to normalize images: {e}")
            return img1_path, img2_path
    
    def imagemagick_compare(self, img1: str, img2: str) -> Dict:
        """Use ImageMagick compare for pixel-perfect analysis"""
        if not self.available_tools['imagemagick']:
            return {'error': 'ImageMagick not available'}
            
        try:
            diff_path = self.output_dir / "imagemagick_diff.png"
            
            # Determine command prefix (new vs legacy)
            cmd_prefix = []
            if self._check_command('magick'):
                cmd_prefix = ['magick', 'compare']
            else:
                cmd_prefix = ['compare']
            
            # Try SSIM first (newer versions), fallback to MSE (older versions)
            ssim_score = 0.0
            psnr_score = 0.0
            mae_score = "0"
            
            # Try SSIM (may not be available in older versions)
            try:
                cmd_ssim = cmd_prefix + [
                    '-metric', 'SSIM',
                    img1, img2,
                    str(diff_path)
                ]
                result_ssim = subprocess.run(cmd_ssim, capture_output=True, text=True)
                if result_ssim.returncode == 0 and result_ssim.stderr.strip():
                    ssim_score = float(result_ssim.stderr.strip())
            except:
                # SSIM not available, try MSE instead
                try:
                    cmd_mse = cmd_prefix + [
                        '-metric', 'MSE',
                        img1, img2,
                        str(diff_path)
                    ]
                    result_mse = subprocess.run(cmd_mse, capture_output=True, text=True)
                    if result_mse.returncode == 0 and result_mse.stderr.strip():
                        mse_value = float(result_mse.stderr.strip().split()[0])
                        # Convert MSE to approximate SSIM (rough approximation)
                        ssim_score = max(0, 1.0 - (mse_value / 10000.0))
                except:
                    ssim_score = 0.0
            
            # Try PSNR
            try:
                cmd_psnr = cmd_prefix + [
                    '-metric', 'PSNR',
                    img1, img2,
                    'null:'
                ]
                result_psnr = subprocess.run(cmd_psnr, capture_output=True, text=True)
                if result_psnr.returncode == 0 and result_psnr.stderr.strip():
                    psnr_score = float(result_psnr.stderr.strip())
            except:
                psnr_score = 0.0
            
            # Try MAE
            try:
                cmd_mae = cmd_prefix + [
                    '-metric', 'MAE',
                    img1, img2,
                    'null:'
                ]
                result_mae = subprocess.run(cmd_mae, capture_output=True, text=True)
                if result_mae.returncode == 0:
                    mae_score = result_mae.stderr.strip() if result_mae.stderr.strip() else "0"
            except:
                mae_score = "0"
            
            return {
                'tool': 'ImageMagick',
                'ssim': ssim_score,
                'psnr': psnr_score,
                'mae': mae_score,
                'diff_image': str(diff_path.relative_to(self.output_dir)),
                'interpretation': self._interpret_imagemagick_scores(ssim_score, psnr_score)
            }
            
        except Exception as e:
            return {'error': f'ImageMagick analysis failed: {e}'}
    
    def perceptualdiff_compare(self, img1: str, img2: str) -> Dict:
        """Use perceptualdiff for perceptual analysis"""
        if not self.available_tools['perceptualdiff']:
            return {'error': 'perceptualdiff not available'}
            
        try:
            diff_path = self.output_dir / "perceptualdiff_diff.png"
            
            cmd = [
                'perceptualdiff',
                '-output', str(diff_path),
                '-verbose',
                img1, img2
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Parse output for metrics
            passed = result.returncode == 0
            output_lines = result.stdout.split('\n') if result.stdout else []
            
            metrics = {'passed': passed}
            for line in output_lines:
                if 'pixels' in line.lower():
                    metrics['details'] = line.strip()
                    
            return {
                'tool': 'perceptualdiff',
                'passed': passed,
                'details': metrics.get('details', ''),
                'diff_image': str(diff_path.relative_to(self.output_dir)) if diff_path.exists() else None,
                'interpretation': 'Images are perceptually similar' if passed else 'Perceptual differences detected'
            }
            
        except Exception as e:
            return {'error': f'perceptualdiff analysis failed: {e}'}
    
    def dssim_compare(self, img1: str, img2: str) -> Dict:
        """Use dssim for structural similarity analysis"""
        if not self.available_tools['dssim']:
            return {'error': 'dssim not available'}
            
        try:
            cmd = ['dssim', img1, img2]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                dssim_score = float(result.stdout.strip().split()[0])
                
                return {
                    'tool': 'dssim',
                    'dssim_score': dssim_score,
                    'ssim_equivalent': 1.0 - dssim_score,
                    'interpretation': self._interpret_dssim_score(dssim_score)
                }
            else:
                return {'error': f'dssim failed: {result.stderr}'}
                
        except Exception as e:
            return {'error': f'dssim analysis failed: {e}'}
    
    def butteraugli_compare(self, img1: str, img2: str) -> Dict:
        """Use butteraugli for advanced perceptual analysis"""
        if not self.available_tools['butteraugli']:
            return {'error': 'butteraugli not available'}
            
        try:
            cmd = ['butteraugli', img1, img2]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                # Parse butteraugli output
                lines = result.stdout.strip().split('\n')
                distance = None
                
                for line in lines:
                    if 'distance' in line.lower() or line.replace('.', '').isdigit():
                        try:
                            distance = float(line.strip())
                            break
                        except ValueError:
                            continue
                
                if distance is not None:
                    return {
                        'tool': 'butteraugli',
                        'perceptual_distance': distance,
                        'interpretation': self._interpret_butteraugli_score(distance)
                    }
                else:
                    return {'error': 'Could not parse butteraugli output'}
            else:
                return {'error': f'butteraugli failed: {result.stderr}'}
                
        except Exception as e:
            return {'error': f'butteraugli analysis failed: {e}'}
    
    def vips_compare(self, img1: str, img2: str) -> Dict:
        """Use vips for fast statistical analysis"""
        if not self.available_tools['vips']:
            return {'error': 'vips not available'}
            
        try:
            # Try different vips commands for statistics
            stats_data = {}
            
            # Try avg command for basic statistics
            try:
                cmd_avg1 = ['vips', 'avg', img1]
                cmd_avg2 = ['vips', 'avg', img2]
                
                avg1_result = subprocess.run(cmd_avg1, capture_output=True, text=True)
                avg2_result = subprocess.run(cmd_avg2, capture_output=True, text=True)
                
                if avg1_result.returncode == 0 and avg2_result.returncode == 0:
                    avg1 = float(avg1_result.stdout.strip())
                    avg2 = float(avg2_result.stdout.strip())
                    stats_data['avg_difference'] = abs(avg1 - avg2)
                    stats_data['avg_image1'] = avg1
                    stats_data['avg_image2'] = avg2
            except:
                pass
            
            # Try deviate command for standard deviation
            try:
                cmd_dev1 = ['vips', 'deviate', img1]
                cmd_dev2 = ['vips', 'deviate', img2]
                
                dev1_result = subprocess.run(cmd_dev1, capture_output=True, text=True)
                dev2_result = subprocess.run(cmd_dev2, capture_output=True, text=True)
                
                if dev1_result.returncode == 0 and dev2_result.returncode == 0:
                    dev1 = float(dev1_result.stdout.strip())
                    dev2 = float(dev2_result.stdout.strip())
                    stats_data['deviation_difference'] = abs(dev1 - dev2)
                    stats_data['deviation_image1'] = dev1
                    stats_data['deviation_image2'] = dev2
            except:
                pass
            
            # Calculate similarity score based on available metrics
            similarity_score = 1.0
            if 'avg_difference' in stats_data:
                # Normalize average difference to similarity (rough approximation)
                similarity_score *= max(0, 1.0 - (stats_data['avg_difference'] / 255.0))
            
            if stats_data:
                stats_data['similarity_estimate'] = similarity_score
                return {
                    'tool': 'vips',
                    'statistics': stats_data,
                    'interpretation': f'Statistical similarity: {similarity_score:.2%}'
                }
            else:
                return {'error': 'No vips statistics could be calculated'}
                
        except Exception as e:
            return {'error': f'vips analysis failed: {e}'}
    
    def _interpret_imagemagick_scores(self, ssim: float, psnr: float) -> str:
        """Interpret ImageMagick SSIM and PSNR scores"""
        if ssim > 0.99:
            return "Excellent similarity (>99%)"
        elif ssim > 0.95:
            return "Very good similarity (95-99%)"
        elif ssim > 0.90:
            return "Good similarity (90-95%)"
        elif ssim > 0.80:
            return "Moderate similarity (80-90%)"
        else:
            return "Poor similarity (<80%)"
    
    def _interpret_dssim_score(self, dssim: float) -> str:
        """Interpret DSSIM score"""
        if dssim < 0.01:
            return "Excellent structural similarity"
        elif dssim < 0.05:
            return "Very good structural similarity"
        elif dssim < 0.10:
            return "Good structural similarity"
        elif dssim < 0.20:
            return "Moderate structural similarity"
        else:
            return "Poor structural similarity"
    
    def _interpret_butteraugli_score(self, distance: float) -> str:
        """Interpret Butteraugli perceptual distance"""
        if distance < 1.0:
            return "Imperceptible differences"
        elif distance < 2.0:
            return "Barely perceptible differences"
        elif distance < 3.0:
            return "Noticeable differences"
        elif distance < 5.0:
            return "Clearly visible differences"
        else:
            return "Significant perceptual differences"
    
    def run_ai_analysis(self, img1: str, img2: str, tool_results: Dict) -> Dict:
        """Coordinate AI analysis from multiple sources"""
        ai_results = {}
        
        # Prepare analysis prompt
        prompt = self._create_ai_analysis_prompt(tool_results)
        
        # Note: In a real implementation, you would call actual AI APIs here
        # For now, we'll create a structured analysis based on tool results
        
        ai_results['claude_analysis'] = self._simulate_claude_analysis(tool_results)
        ai_results['synthesis'] = self._synthesize_results(tool_results)
        
        return ai_results
    
    def _create_ai_analysis_prompt(self, tool_results: Dict) -> str:
        """Create comprehensive prompt for AI analysis"""
        prompt = """
        Analyze these visual diff tool results for pixel-perfect website cloning:
        
        Tool Results:
        """
        
        for tool, result in tool_results.items():
            if 'error' not in result:
                prompt += f"\n{tool.upper()}:\n"
                for key, value in result.items():
                    if key != 'tool':
                        prompt += f"  {key}: {value}\n"
        
        prompt += """
        
        Please provide:
        1. Overall similarity assessment (0-100%)
        2. Critical differences that need attention
        3. Recommendations for achieving pixel-perfect match
        4. Priority areas for improvement
        5. Assessment of readiness for production
        """
        
        return prompt
    
    def _simulate_claude_analysis(self, tool_results: Dict) -> Dict:
        """Simulate comprehensive Claude analysis"""
        # Extract key metrics
        ssim_score = 0.0
        perceptual_passed = False
        dssim_score = 1.0
        butteraugli_distance = 10.0
        
        for tool, result in tool_results.items():
            if 'error' not in result:
                if 'ssim' in result:
                    ssim_score = result['ssim']
                if 'passed' in result:
                    perceptual_passed = result['passed']
                if 'dssim_score' in result:
                    dssim_score = result['dssim_score']
                if 'perceptual_distance' in result:
                    butteraugli_distance = result['perceptual_distance']
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(ssim_score, perceptual_passed, dssim_score, butteraugli_distance)
        
        return {
            'overall_similarity': f"{overall_score:.1f}%",
            'readiness_assessment': self._assess_readiness(overall_score),
            'critical_issues': self._identify_critical_issues(tool_results),
            'recommendations': self._generate_recommendations(tool_results, overall_score),
            'confidence': 'High' if len([r for r in tool_results.values() if 'error' not in r]) >= 3 else 'Medium'
        }
    
    def _calculate_overall_score(self, ssim: float, perceptual_passed: bool, dssim: float, butteraugli: float) -> float:
        """Calculate weighted overall similarity score"""
        scores = []
        
        if ssim > 0:
            scores.append(ssim * 100)
        
        if perceptual_passed:
            scores.append(95.0)
        else:
            scores.append(70.0)
        
        if dssim < 1.0:
            scores.append((1.0 - dssim) * 100)
        
        if butteraugli < 10.0:
            scores.append(max(0, 100 - butteraugli * 10))
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _assess_readiness(self, score: float) -> str:
        """Assess production readiness"""
        if score >= 95:
            return "Production Ready - Excellent match"
        elif score >= 90:
            return "Nearly Ready - Minor adjustments needed"
        elif score >= 80:
            return "Needs Work - Moderate differences detected"
        elif score >= 70:
            return "Significant Issues - Major differences present"
        else:
            return "Not Ready - Substantial reconstruction needed"
    
    def _identify_critical_issues(self, tool_results: Dict) -> List[str]:
        """Identify critical issues from tool results"""
        issues = []
        
        for tool, result in tool_results.items():
            if 'error' in result:
                issues.append(f"{tool} analysis failed: {result['error']}")
                continue
                
            if tool == 'imagemagick' and 'ssim' in result:
                if result['ssim'] < 0.9:
                    issues.append(f"Low SSIM score ({result['ssim']:.3f}) indicates structural differences")
                    
            if tool == 'perceptualdiff' and 'passed' in result:
                if not result['passed']:
                    issues.append("Perceptual differences detected by human vision model")
                    
            if tool == 'butteraugli' and 'perceptual_distance' in result:
                if result['perceptual_distance'] > 3.0:
                    issues.append(f"High perceptual distance ({result['perceptual_distance']:.2f}) detected")
        
        return issues if issues else ["No critical issues detected"]
    
    def _generate_recommendations(self, tool_results: Dict, overall_score: float) -> List[str]:
        """Generate specific recommendations"""
        recommendations = []
        
        if overall_score < 90:
            recommendations.extend([
                "Review color accuracy and ensure consistent color profiles",
                "Check image compression settings and quality levels",
                "Verify font rendering and text positioning",
                "Analyze layout spacing and alignment precision"
            ])
        
        if overall_score < 80:
            recommendations.extend([
                "Consider implementing automated screenshot comparison",
                "Review responsive breakpoints and media queries",
                "Check for missing or incorrectly sized assets",
                "Audit CSS inheritance and specificity issues"
            ])
        
        if overall_score < 70:
            recommendations.extend([
                "Perform comprehensive design system audit",
                "Review fundamental layout structure",
                "Consider starting from scratch with tighter controls",
                "Implement stricter asset management processes"
            ])
        
        return recommendations
    
    def _synthesize_results(self, tool_results: Dict) -> Dict:
        """Synthesize all tool results into actionable insights"""
        working_tools = [tool for tool, result in tool_results.items() if 'error' not in result]
        failed_tools = [tool for tool, result in tool_results.items() if 'error' in result]
        
        return {
            'tools_used': working_tools,
            'tools_failed': failed_tools,
            'consensus': self._determine_consensus(tool_results),
            'confidence_level': len(working_tools) / len(tool_results.keys()) if tool_results else 0.0,
            'next_steps': self._suggest_next_steps(tool_results)
        }
    
    def _determine_consensus(self, tool_results: Dict) -> str:
        """Determine consensus from multiple tools"""
        positive_results = 0
        total_results = 0
        
        for result in tool_results.values():
            if 'error' in result:
                continue
                
            total_results += 1
            
            # Check various positive indicators
            if (('ssim' in result and result['ssim'] > 0.9) or
                ('passed' in result and result['passed']) or
                ('dssim_score' in result and result['dssim_score'] < 0.1) or
                ('perceptual_distance' in result and result['perceptual_distance'] < 2.0)):
                positive_results += 1
        
        if total_results == 0:
            return "No consensus possible - all tools failed"
        
        consensus_ratio = positive_results / total_results
        
        if consensus_ratio >= 0.8:
            return "Strong consensus: Images are very similar"
        elif consensus_ratio >= 0.6:
            return "Moderate consensus: Images are reasonably similar"
        elif consensus_ratio >= 0.4:
            return "Weak consensus: Mixed results"
        else:
            return "Strong consensus: Significant differences detected"
    
    def _suggest_next_steps(self, tool_results: Dict) -> List[str]:
        """Suggest concrete next steps based on results"""
        steps = []
        
        working_tools = len([r for r in tool_results.values() if 'error' not in r])
        
        if working_tools < 3:
            steps.append("Install missing visual diff tools for more comprehensive analysis")
        
        steps.extend([
            "Generate detailed diff images for visual inspection",
            "Run analysis on additional page sections",
            "Test responsive breakpoints",
            "Validate cross-browser consistency"
        ])
        
        return steps
    
    def generate_comprehensive_report(self, img1: str, img2: str, tool_results: Dict, ai_analysis: Dict) -> Dict:
        """Generate final comprehensive report"""
        # Generate summary statistics
        summary = {
            'timestamp': time.time(),
            'image1': img1,
            'image2': img2,
            'tools_available': sum(self.available_tools.values()),
            'tools_used': len([r for r in tool_results.values() if 'error' not in r]),
            'overall_assessment': ai_analysis.get('claude_analysis', {}).get('overall_similarity', 'Unknown'),
            'readiness': ai_analysis.get('claude_analysis', {}).get('readiness_assessment', 'Unknown'),
            'critical_issues_count': len(ai_analysis.get('claude_analysis', {}).get('critical_issues', [])),
            'recommendations_count': len(ai_analysis.get('claude_analysis', {}).get('recommendations', []))
        }
        
        return {
            'metadata': {
                'analysis_timestamp': time.time(),
                'tool_versions': self._get_tool_versions(),
                'image_info': self._get_image_info(img1, img2)
            },
            'tool_results': tool_results,
            'ai_analysis': ai_analysis,
            'summary': summary,
            'output_directory': str(self.output_dir)
        }
    
    def _get_tool_versions(self) -> Dict[str, str]:
        """Get versions of available tools"""
        versions = {}
        
        for tool, available in self.available_tools.items():
            if available:
                try:
                    if tool == 'imagemagick':
                        result = subprocess.run(['magick', '--version'], capture_output=True, text=True)
                    elif tool == 'vips':
                        result = subprocess.run(['vips', '--version'], capture_output=True, text=True)
                    else:
                        result = subprocess.run([tool, '--version'], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        versions[tool] = result.stdout.split('\n')[0]
                    else:
                        versions[tool] = "Version unknown"
                except:
                    versions[tool] = "Version check failed"
            else:
                versions[tool] = "Not available"
        
        return versions
    
    def _get_image_info(self, img1: str, img2: str) -> Dict:
        """Get basic image information"""
        info = {}
        
        for i, img_path in enumerate([img1, img2], 1):
            try:
                with Image.open(img_path) as img:
                    info[f'image{i}'] = {
                        'path': img_path,
                        'size': img.size,
                        'mode': img.mode,
                        'format': img.format
                    }
            except Exception as e:
                info[f'image{i}'] = {'error': str(e)}
        
        return info
    
    def compare_images(self, img1_path: str, img2_path: str) -> Dict:
        """Main method to perform comprehensive visual diff analysis"""
        print(f"🔍 Starting comprehensive visual diff analysis...")
        print(f"📷 Image 1: {img1_path}")
        print(f"📷 Image 2: {img2_path}")
        
        # Ensure images exist
        if not Path(img1_path).exists():
            return {'error': f'Image 1 not found: {img1_path}'}
        if not Path(img2_path).exists():
            return {'error': f'Image 2 not found: {img2_path}'}
        
        # Normalize images
        norm_img1, norm_img2 = self._normalize_images(img1_path, img2_path)
        
        # Ensure compatible formats
        comp_img1 = self._ensure_image_format(norm_img1)
        comp_img2 = self._ensure_image_format(norm_img2)
        
        # Run all available tools
        tool_results = {}
        
        print("\n🛠️ Running visual diff tools...")
        
        if self.available_tools['imagemagick']:
            print("  Running ImageMagick compare...")
            tool_results['imagemagick'] = self.imagemagick_compare(comp_img1, comp_img2)
        
        if self.available_tools['perceptualdiff']:
            print("  Running perceptualdiff...")
            tool_results['perceptualdiff'] = self.perceptualdiff_compare(comp_img1, comp_img2)
        
        if self.available_tools['dssim']:
            print("  Running dssim...")
            tool_results['dssim'] = self.dssim_compare(comp_img1, comp_img2)
        
        if self.available_tools['butteraugli']:
            print("  Running butteraugli...")
            tool_results['butteraugli'] = self.butteraugli_compare(comp_img1, comp_img2)
        
        if self.available_tools['vips']:
            print("  Running vips...")
            tool_results['vips'] = self.vips_compare(comp_img1, comp_img2)
        
        # Run AI analysis
        print("\n🤖 Running AI analysis...")
        ai_analysis = self.run_ai_analysis(comp_img1, comp_img2, tool_results)
        
        # Generate comprehensive report
        print("\n📊 Generating comprehensive report...")
        report = self.generate_comprehensive_report(img1_path, img2_path, tool_results, ai_analysis)
        
        # Save report
        report_path = self.output_dir / f"visual_diff_report_{int(time.time())}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✅ Analysis complete!")
        print(f"📄 Report saved to: {report_path}")
        
        # Print summary
        summary = report['summary']
        print(f"\n📊 SUMMARY:")
        print(f"  Overall Assessment: {summary['overall_assessment']}")
        print(f"  Readiness: {summary['readiness']}")
        print(f"  Tools Used: {summary['tools_used']}/{summary['tools_available']}")
        print(f"  Critical Issues: {summary['critical_issues_count']}")
        
        return report

def main():
    parser = argparse.ArgumentParser(description='Comprehensive Visual Diff Analysis Toolkit')
    parser.add_argument('image1', nargs='?', help='Path to first image')
    parser.add_argument('image2', nargs='?', help='Path to second image')
    parser.add_argument('-o', '--output', help='Output directory for results', 
                       default=f'visual_diff_{int(time.time())}')
    parser.add_argument('--install-check', action='store_true', 
                       help='Check tool installation status')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = VisualDiffAnalyzer(args.output)
    
    if args.install_check:
        print("🔧 Visual Diff Tools Status:")
        for tool, available in analyzer.available_tools.items():
            status = "✅ Available" if available else "❌ Not installed"
            print(f"  {tool}: {status}")
        
        missing_tools = [tool for tool, available in analyzer.available_tools.items() if not available]
        if missing_tools:
            print(f"\n⚠️ Missing tools: {', '.join(missing_tools)}")
            print("Run install_tools.sh to install missing dependencies")
        else:
            print("\n✅ All tools available!")
        
        return 0
    
    if not args.image1 or not args.image2:
        parser.error("image1 and image2 are required unless using --install-check")
    
    try:
        # Run comprehensive analysis
        result = analyzer.compare_images(args.image1, args.image2)
        
        if 'error' in result:
            print(f"💥 Analysis failed: {result['error']}")
            return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted by user")
        return 1
    except Exception as e:
        print(f"💥 Analysis failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())