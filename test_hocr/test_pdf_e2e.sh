#!/bin/bash
# hOCR Optimize end-to-end test script
# Test the complete process directly from the PDF file

set -e # Exit immediately when encountering an error

echo "=========================================="
echo "hOCR Optimization - End-to-End Test"
echo "=========================================="
echo ""

# Check parameters
if [ $# -lt 1 ]; then
    echo "Usage: $0 <PDF file path> [temporary directory]"
    echo ""
    echo "Example:"
    echo "  $0 test.pdf"
    echo "  $0 test.pdf /tmp/my_test"
    echo ""
    exit 1
fi

PDF_FILE="$1"
TEMP_DIR="${2:-/tmp/hocr_test_$(date +%s)}"

# Check PDF file
if [ ! -f "$PDF_FILE" ]; then
    echo "❌ Error: PDF file not found: $PDF_FILE"
    exit 1
fi

echo "📄 Test file: $PDF_FILE"
echo "📂 Temporary directory: $TEMP_DIR"
echo "📊 PDF size: $(du -h "$PDF_FILE" | cut -f1)"
echo ""

#Create temporary directory
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

echo "=========================================="
echo "Step 1/5: Deconstruct PDF → TIFF image"
echo "=========================================="
echo ""

pdftoppm -tiff -tiffcompression lzw -r 300 "$PDF_FILE" page
IMAGE_COUNT=$(ls page-*.tif 2>/dev/null | wc -l)

if [ $IMAGE_COUNT -eq 0 ]; then
    echo "❌ Error: No image files were generated"
    exit 1
fi

echo "✅ Successfully generated $IMAGE_COUNT images"
echo "size: $(du -sh page-*.tif | head -1 | cut -f1) (each)"
echo ""

echo "=========================================="
echo "Step 2/5: OCR recognition → generate original hOCR"
echo "=========================================="
echo ""

# OCR process all images
for img in page-*.tif; do
    base=$(basename "$img" .tif)
    echo "processing: $img"
    tesseract "$img" "$base" -l eng hocr 2>/dev/null
done

# Merge hOCR files
echo ""
echo "Merge hOCR files..."
python3 << 'EOF'
import glob
import re
from pathlib import Path

def merge_hocr_files(output_path):
    """Merge multiple hOCR files"""
    hocr_files = sorted(glob.glob('page-*.hocr'))
    if not hocr_files:
        print("Error: hOCR file not found")
        return False
    
    print(f"{len(hocr_files)} hOCR files found")
    
    # Read the first file as template
    with open(hocr_files[0], 'r', encoding='utf-8') as f:
        content = f.read()
    
    #Extract head and tail
    body_match = re.search(r'<body>(.*?)</body>', content, re.DOTALL)
    if not body_match:
        print("Error: Unable to parse hOCR format")
        return False
    
    header = content[:body_match.start(1)]
    footer = content[body_match.end(1):]
    
    # Collect all page content
    all_pages = []
    for hocr_file in hocr_files:
        with open(hocr_file, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # Extract page content in body
        page_match = re.search(r'<body>(.*?)</body>', file_content, re.DOTALL)
        if page_match:
            all_pages.append(page_match.group(1))
    
    # merge
    merged_content = header + '\n'.join(all_pages) + footer
    
    #Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(merged_content)
    
    print(f"✅ Merger completed: {output_path}")
    return True

merge_hocr_files('combined_original.hocr')
EOF

if [ ! -f "combined_original.hocr" ]; then
    echo "❌ Error: Merge hOCR failed"
    exit 1
fi

ORIGINAL_HOCR_SIZE=$(du -h combined_original.hocr | cut -f1)
echo "✅ 原始 hOCR: combined_original.hocr ($ORIGINAL_HOCR_SIZE)"
echo ""

echo "=========================================="
echo "Step 3/5: Optimize hOCR → Delete ocrx_word"
echo "=========================================="
echo ""

python3 << 'EOF'
import re

def optimize_hocr_no_words(input_file, output_file):
    """Delete all ocrx_word tags"""
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Delete the ocrx_word tag (including its content)
    optimized = re.sub(
        r"<span class='ocrx_word'[^>]*>.*?</span>",
        '',
        content,
        flags=re.DOTALL
    )
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(optimized)
    
    original_size = len(content)
    optimized_size = len(optimized)
    reduction = (1 - optimized_size / original_size) * 100
    
    print(f"Original size: {original_size:,} bytes")
    print(f"After optimization: {optimized_size:,} bytes")
    print(f"Reduction: {reduction:.1f}%")
    
    return True

optimize_hocr_no_words('combined_original.hocr', 'combined_no_words.hocr')
EOF

if [ ! -f "combined_no_words.hocr" ]; then
    echo "❌ Error: Optimizing hOCR failed"
    exit 1
fi

OPTIMIZED_HOCR_SIZE=$(du -h combined_no_words.hocr | cut -f1)
echo "✅ 优化 hOCR: combined_no_words.hocr ($OPTIMIZED_HOCR_SIZE)"
echo ""

echo "=========================================="
echo "Step 4/5: Generate test PDF"
echo "=========================================="
echo ""

#Test 1: Using original hOCR
echo "[Test 1] Generate PDF using raw hOCR..."
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined_original.hocr \
    --dpi 300 \
    --bg-downsample 2 \
    -J grok \
    -o test_original.pdf

if [ -f "test_original.pdf" ]; then
    ORIGINAL_PDF_SIZE=$(du -h test_original.pdf | cut -f1)
    echo "✅ Original version: test_original.pdf ($ORIGINAL_PDF_SIZE)"
else
    echo "⚠️ Original version generation failed"
fi
echo ""

#Test 2: Using optimized hOCR
echo "[Test 2] Generate PDF using optimized hOCR (no_words)..."
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined_no_words.hocr \
    --dpi 300 \
    --bg-downsample 2 \
    -J grok \
    -o test_no_words.pdf

if [ -f "test_no_words.pdf" ]; then
    OPTIMIZED_PDF_SIZE=$(du -h test_no_words.pdf | cut -f1)
    echo "✅ Optimized version: test_no_words.pdf ($OPTIMIZED_PDF_SIZE)"
else
    echo "❌ Optimized version generation failed"
    exit 1
fi
echo ""

echo "=========================================="
echo "Step 5/5: Result Analysis"
echo "=========================================="
echo ""

# Detailed comparison
ls -lh test_*.pdf combined_*.hocr

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Summary of test results"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Original hOCR: $ORIGINAL_HOCR_SIZE"
echo "Optimize hOCR: $OPTIMIZED_HOCR_SIZE"
echo ""

if [ -f "test_original.pdf" ]; then
    echo "Original PDF: $ORIGINAL_PDF_SIZE"
fi
echo "Optimize PDF: $OPTIMIZED_PDF_SIZE"
echo ""

# Calculate savings
if [ -f "test_original.pdf" ]; then
    ORIGINAL_BYTES=$(stat -f%z test_original.pdf 2>/dev/null || stat -c%s test_original.pdf)
    OPTIMIZED_BYTES=$(stat -f%z test_no_words.pdf 2>/dev/null || stat -c%s test_no_words.pdf)
    SAVED_BYTES=$((ORIGINAL_BYTES - OPTIMIZED_BYTES))
    SAVED_MB=$(echo "scale=2; $SAVED_BYTES / 1024 / 1024" | bc)
    SAVED_PCT=$(echo "scale=1; $SAVED_BYTES * 100 / $ORIGINAL_BYTES" | bc)
    
    if [ $SAVED_BYTES -gt 0 ]; then
        echo "💾 Save space: ${SAVED_MB} MB (${SAVED_PCT}%)"
    elif [ $SAVED_BYTES -lt 0 ]; then
        echo "⚠️ After optimization, it has increased in size. $(echo "scale=2; -$SAVED_BYTES / 1024 / 1024" | bc) MB"
    else
        echo "📊 Basically the same size"
    fi
fi

echo ""
echo "📁 All file locations: $TEMP_DIR"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Test completed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next:"
echo "1. Check PDF quality:"
echo "   cd $TEMP_DIR"
echo " # Copy PDF to Windows for viewing"
echo ""
echo "2. Test searchability:"
echo "Open test_original.pdf and test_no_words.pdf"
echo "Try to search text (Ctrl+F)"
echo ""
echo "3. If successful, integrate into the project:"
echo "-Modify pipeline.py to add hOCR optimization"
echo "-release v2.1.0"
