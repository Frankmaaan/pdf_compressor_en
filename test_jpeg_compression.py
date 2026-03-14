#!/usr/bin/env python3
"""
JPEG compression quality test script

Test the impact of different JPEG quality parameters on file size and OCR recognition rate.
Helps choose optimal quality parameters (target: ~1MB/page).
"""

import sys
import subprocess
import tempfile
from pathlib import Path


def test_jpeg_quality(pdf_file, dpi=300):
    """Test different JPEG quality settings"""
    
    if not Path(pdf_file).exists():
        print(f"❌ Error: PDF file does not exist: {pdf_file}")
        return
    
    print("=" * 70)
    print("JPEG compression quality test")
    print("=" * 70)
    print(f"Input file: {pdf_file}")
    print(f"DPI: {dpi}")
    print()
    
    # Test different quality parameters
    qualities = [70, 75, 80, 85, 90, 95]
    
    results = []
    
    with tempfile.TemporaryDirectory() as temp_dir:
        for quality in qualities:
            print(f"\n{'─' * 70}")
            print(f"Test JPEG quality: {quality}")
            print(f"{'─' * 70}")
            
            output_prefix = Path(temp_dir) / f"test_q{quality}"
            
            # Generate JPEG image (first page only)
            cmd = [
                "pdftoppm",
                "-jpeg",
                "-jpegopt", f"quality={quality}",
                "-r", str(dpi),
                "-f", "1", # first page only
                "-l", "1", # first page only
                str(pdf_file),
                str(output_prefix)
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode != 0:
                    print(f" ❌ pdftoppm failed: {result.stderr}")
                    continue
                
                # Find generated files
                jpg_file = output_prefix.parent / f"{output_prefix.name}-1.jpg"
                
                if not jpg_file.exists():
                    print(f" ❌ Generated file not found: {jpg_file}")
                    continue
                
                # Get file size
                file_size_bytes = jpg_file.stat().st_size
                file_size_mb = file_size_bytes / 1024 / 1024
                
                print(f" ✓ File size: {file_size_mb:.2f} MB ({file_size_bytes:,} bytes)")
                
                # Optional: test OCR (if tesseract is installed)
                ocr_text = ""
                try:
                    ocr_result = subprocess.run(
                        ["tesseract", str(jpg_file), "stdout", "-l", "eng"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if ocr_result.returncode == 0:
                        ocr_text = ocr_result.stdout.strip()
                        char_count = len(ocr_text)
                        print(f" ✓ Number of characters recognized by OCR: {char_count}")
                    else:
                        print(f" ⚠️ OCR failed (tesseract may not be installed)")
                except FileNotFoundError:
                    print(f" ⚠️ tesseract is not installed, skip OCR test")
                except subprocess.TimeoutExpired:
                    print(f" ⚠️ OCR timeout")
                
                results.append({
                    'quality': quality,
                    'size_mb': file_size_mb,
                    'size_bytes': file_size_bytes,
                    'ocr_chars': len(ocr_text) if ocr_text else 0
                })
                
            except subprocess.TimeoutExpired:
                print(f" ❌ command timeout")
            except Exception as e:
                print(f" ❌ Error: {e}")
    
    #Print summary results
    print("\n" + "=" * 70)
    print("Summary of test results")
    print("=" * 70)
    print(f"{'quality':<10} {'file size':<15} {'compression ratio':<15} {'number of OCR characters':<15} {'recommended':<10}")
    print("─" * 70)
    
    for r in results:
        compression_ratio = (1 - r['size_mb'] / 25.0) * 100 # Assume original 25MB
        recommendation = ""
        
        # Give recommendations based on target 1MB
        if 0.8 <= r['size_mb'] <= 1.5:
            recommendation = "⭐ recommendation"
        elif r['size_mb'] < 0.8:
            recommendation = "Maybe too small"
        else:
            recommendation = "Slightly larger"
        
        print(f"{r['quality']:<10} {r['size_mb']:.2f} MB{'':<7} "
              f"{compression_ratio:.1f}%{'':<8} "
              f"{r['ocr_chars']:<15} {recommendation:<10}")
    
    print("\n" + "=" * 70)
    print("Suggestion:")
    print("=" * 70)
    
    # Find the quality setting closest to 1MB
    target_size = 1.0
    best_match = min(results, key=lambda x: abs(x['size_mb'] - target_size))
    
    print(f"• Target file size: about 1 MB")
    print(f"• Recommended JPEG quality: {best_match['quality']}")
    print(f"• Expected file size: {best_match['size_mb']:.2f} MB")
    print(f"• Compression rate: {(1 - best_match['size_mb'] / 25.0) * 100:.1f}%")
    print()
    print("Modify compressor/pipeline.py:")
    print(f'  command = ["pdftoppm", "-jpeg", "-jpegopt", "quality={best_match["quality"]}", ...]')
    print()
    print("⚠️ Note:")
    print(" - JPEG is lossy compression and will slightly reduce image quality")
    print(" - usually has little impact on OCR recognition rate (quality ≥ 75)")
    print(" - If you find that the OCR recognition rate drops, you can increase the quality parameters appropriately")
    print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python test_jpeg_compression.py <pdf_file> [dpi]")
        print()
        print("Example:")
        print("  python test_jpeg_compression.py testpdf.pdf")
        print("  python test_jpeg_compression.py testpdf.pdf 300")
        return 1
    
    pdf_file = sys.argv[1]
    dpi = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    
    test_jpeg_quality(pdf_file, dpi)
    return 0


if __name__ == '__main__':
    sys.exit(main())
