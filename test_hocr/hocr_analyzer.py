"""
hOCR file analysis and optimization tools

Function:
1. Analyze hOCR file structure
2. Experimental deletion of different parts
3. Measure file size changes
4. Evaluate the impact on PDF generation
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple
import logging

class HocrAnalyzer:
    """hOCR File Analyzer"""
    
    def __init__(self, hocr_file: Path):
        self.hocr_file = Path(hocr_file)
        self.original_size = self.hocr_file.stat().st_size
        
        # Read file content
        with open(self.hocr_file, 'r', encoding='utf-8') as f:
            self.content = f.read()
        
        print(f"📄 Original hOCR file: {self.hocr_file.name}")
        print(f"📊 Original size: {self.original_size / 1024 / 1024:.2f} MB")
        print(f"📏 Original number of lines: {len(self.content.splitlines())}")
    
    def analyze_structure(self) -> Dict:
        """Analyze the basic structure of hOCR files"""
        print("\n" + "="*70)
        print("🔍 hOCR file structure analysis")
        print("="*70)
        
        analysis = {
            'total_size': self.original_size,
            'total_lines': len(self.content.splitlines()),
            'elements': {}
        }
        
        # Analyze various HTML tags
        tags = [
            ('ocr_page', 'Page container'),
            ('ocr_carea', 'content area'),
            ('ocr_par', 'paragraph'),
            ('ocr_line', 'Text line'),
            ('ocrx_word', 'word/phrase'),
        ]
        
        for tag_class, description in tags:
            pattern = rf"class=['\"].*?{tag_class}.*?['\"]"
            matches = re.findall(pattern, self.content)
            analysis['elements'][tag_class] = {
                'count': len(matches),
                'description': description
            }
            print(f"  📌 {tag_class:15} ({description:10}): {len(matches):6} 个")
        
        #Analyze text content size
        text_pattern = r'<span[^>]*?ocrx_word[^>]*?>([^<]+)</span>'
        text_matches = re.findall(text_pattern, self.content)
        total_text_size = sum(len(text.encode('utf-8')) for text in text_matches)
        
        print(f"\n 💬 Text content:")
        print(f" - Number of words: {len(text_matches)}")
        print(f" - text size: {total_text_size / 1024:.2f} KB")
        print(f" - Proportion: {total_text_size / self.original_size * 100:.1f}%")
        
        analysis['text_content'] = {
            'word_count': len(text_matches),
            'text_size': total_text_size,
            'percentage': total_text_size / self.original_size * 100
        }
        
        # Analyze bbox information
        bbox_pattern = r"bbox \d+ \d+ \d+ \d+"
        bbox_matches = re.findall(bbox_pattern, self.content)
        bbox_size = sum(len(bbox.encode('utf-8')) for bbox in bbox_matches)
        
        print(f"\n 📍 coordinate information (bbox):")
        print(f" - bbox number: {len(bbox_matches)}")
        print(f" - bbox size: {bbox_size / 1024:.2f} KB")
        print(f" - Proportion: {bbox_size / self.original_size * 100:.1f}%")
        
        analysis['bbox_info'] = {
            'count': len(bbox_matches),
            'size': bbox_size,
            'percentage': bbox_size / self.original_size * 100
        }
        
        return analysis
    
    def create_empty_hocr(self, output_file: Path) -> Tuple[Path, int]:
        """
        Create empty hOCR - remove all text content, retain structure
        
        Strategy: Remove the text content within the <span class="ocrx_word"> tag
        """
        print("\n" + "="*70)
        print("🧪 Experiment 1: Create empty hOCR (remove text content)")
        print("="*70)
        
        # Delete the text content in the ocrx_word tag
        empty_content = re.sub(
            r'(<span[^>]*?ocrx_word[^>]*?>)([^<]+)(</span>)',
            r'\1\3', # Keep start and end tags, delete text
            self.content
        )
        
        output_file.write_text(empty_content, encoding='utf-8')
        new_size = output_file.stat().st_size
        reduction = self.original_size - new_size
        percentage = (reduction / self.original_size) * 100
        
        print(f" ✅ Created: {output_file.name}")
        print(f" 📊 New size: {new_size / 1024 / 1024:.2f} MB")
        print(f" 📉 Reduction: {reduction / 1024 / 1024:.2f} MB ({percentage:.1f}%)")
        
        return output_file, new_size
    
    def create_minimal_hocr(self, output_file: Path) -> Tuple[Path, int]:
        """
        Create minimal hOCR - keep only page structure and bbox
        
        Strategy: Remove all text content and unnecessary attributes
        """
        print("\n" + "="*70)
        print("🧪 Experiment 2: Create minimal hOCR (keep only necessary structures)")
        print("="*70)
        
        minimal_content = self.content
        
        # Step 1: Delete text content
        minimal_content = re.sub(
            r'(<span[^>]*?ocrx_word[^>]*?>)([^<]+)(</span>)',
            r'\1\3',
            minimal_content
        )
        
        # Step 2: Simplify the title attribute (only keep bbox)
        def simplify_title(match):
            full_title = match.group(1)
            bbox_match = re.search(r'bbox \d+ \d+ \d+ \d+', full_title)
            if bbox_match:
                return f'title="{bbox_match.group()}"'
            return match.group(0)
        
        minimal_content = re.sub(
            r'title="([^"]*)"',
            simplify_title,
            minimal_content
        )
        
        output_file.write_text(minimal_content, encoding='utf-8')
        new_size = output_file.stat().st_size
        reduction = self.original_size - new_size
        percentage = (reduction / self.original_size) * 100
        
        print(f" ✅ Created: {output_file.name}")
        print(f" 📊 New size: {new_size / 1024 / 1024:.2f} MB")
        print(f" 📉 Reduction: {reduction / 1024 / 1024:.2f} MB ({percentage:.1f}%)")
        
        return output_file, new_size
    
    def create_no_words_hocr(self, output_file: Path) -> Tuple[Path, int]:
        """
        Create wordless hOCR - remove all ocrx_word tags
        
        Strategy: Remove <span class="ocrx_word"> tag completely
        """
        print("\n" + "="*70)
        print("🧪 Experiment 3: Creating wordless hOCR (removing ocrx_word tag)")
        print("="*70)
        
        # Delete the entire ocrx_word span tag
        no_words_content = re.sub(
            r'<span[^>]*?ocrx_word[^>]*?>.*?</span>\s*',
            '',
            self.content
        )
        
        output_file.write_text(no_words_content, encoding='utf-8')
        new_size = output_file.stat().st_size
        reduction = self.original_size - new_size
        percentage = (reduction / self.original_size) * 100
        
        print(f" ✅Created: {output_file.name}")
        print(f" 📊 New size: {new_size / 1024 / 1024:.2f} MB")
        print(f" 📉 Reduction: {reduction / 1024 / 1024:.2f} MB ({percentage:.1f}%)")
        
        return output_file, new_size
    
    def create_no_lines_hocr(self, output_file: Path) -> Tuple[Path, int]:
        """
        Create textless lines hOCR - remove all ocr_line tags
        
        Strategy: Remove <span class="ocr_line"> tag and its content
        """
        print("\n" + "="*70)
        print("🧪 Experiment 4: Create textless lines hOCR (remove ocr_line tag)")
        print("="*70)
        
        # Delete the entire ocr_line span tag
        no_lines_content = re.sub(
            r'<span[^>]*?ocr_line[^>]*?>.*?</span>\s*',
            '',
            self.content,
            flags=re.DOTALL
        )
        
        output_file.write_text(no_lines_content, encoding='utf-8')
        new_size = output_file.stat().st_size
        reduction = self.original_size - new_size
        percentage = (reduction / self.original_size) * 100
        
        print(f" ✅ Created: {output_file.name}")
        print(f" 📊 New size: {new_size / 1024 / 1024:.2f} MB")
        print(f" 📉 Reduction: {reduction / 1024 / 1024:.2f} MB ({percentage:.1f}%)")
        
        return output_file, new_size
    
    def show_sample(self, lines: int = 50):
        """Display sample content of hOCR file"""
        print("\n" + "="*70)
        print(f"📝 hOCR file sample (first {lines} lines)")
        print("="*70)
        
        content_lines = self.content.splitlines()
        for i, line in enumerate(content_lines[:lines], 1):
            print(f"{i:3}: {line}")
        
        if len(content_lines) > lines:
            print(f"\n... (omit {len(content_lines) - lines} lines)")


def run_hocr_experiments(hocr_file: Path):
    """Run a complete hOCR optimization experiment"""
    
    print("\n" + "="*70)
    print("🔬 hOCR file optimization research experiment")
    print("="*70)
    print(f"📅 Date: 2025-10-19")
    print(f"🎯 Goal: Study hOCR file optimization to reduce final PDF size")
    print("="*70)
    
    #Create output directory
    output_dir = hocr_file.parent / "hocr_experiments"
    output_dir.mkdir(exist_ok=True)
    
    #Initialize analyzer
    analyzer = HocrAnalyzer(hocr_file)
    
    # show sample
    analyzer.show_sample(30)
    
    # Analyze structure
    analysis = analyzer.analyze_structure()
    
    # Run various optimization experiments
    experiments = []
    
    # Experiment 1: Empty hOCR (remove text)
    exp1_file = output_dir / "combined_empty.hocr"
    exp1_path, exp1_size = analyzer.create_empty_hocr(exp1_file)
    experiments.append(('empty text', exp1_size))
    
    # Experiment 2: Minimal hOCR (only keep bbox)
    exp2_file = output_dir / "combined_minimal.hocr"
    exp2_path, exp2_size = analyzer.create_minimal_hocr(exp2_file)
    experiments.append(('minimize', exp2_size))
    
    # Experiment 3: No word hOCR
    exp3_file = output_dir / "combined_no_words.hocr"
    exp3_path, exp3_size = analyzer.create_no_words_hocr(exp3_file)
    experiments.append(('no word', exp3_size))
    
    # Experiment 4: No text lines hOCR
    exp4_file = output_dir / "combined_no_lines.hocr"
    exp4_path, exp4_size = analyzer.create_no_lines_hocr(exp4_file)
    experiments.append(('No text line', exp4_size))
    
    # Summary comparison
    print("\n" + "="*70)
    print("📊 Experimental results comparison")
    print("="*70)
    print(f"\n{'Type':<12} {'Size (MB)':<12} {'Reduction (MB)':<12} {'Reduction rate':<10}")
    print("-" * 70)
    
    original_mb = analyzer.original_size / 1024 / 1024
    print(f"{'original':<12} {original_mb:<12.2f} {'-':<12} {'-':<10}")
    
    for name, size in experiments:
        size_mb = size / 1024 / 1024
        reduction_mb = (analyzer.original_size - size) / 1024 / 1024
        reduction_pct = (analyzer.original_size - size) / analyzer.original_size * 100
        print(f"{name:<12} {size_mb:<12.2f} {reduction_mb:<12.2f} {reduction_pct:<10.1f}%")
    
    print("\n" + "="*70)
    print("✅ Experiment completed! All variations have been saved to:", output_dir)
    print("="*70)
    
    return output_dir, analysis


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python hocr_analyzer.py <hocr_file>")
        print("\nExample: python hocr_analyzer.py /tmp/tmpxxx/combined.hocr")
        sys.exit(1)
    
    hocr_file = Path(sys.argv[1])
    
    if not hocr_file.exists():
        print(f"❌ Error: File does not exist: {hocr_file}")
        sys.exit(1)
    
    run_hocr_experiments(hocr_file)
