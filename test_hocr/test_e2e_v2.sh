#!/bin/bash
# Fast hOCR optimization test - directly use PDF files (improved version)

set -e # Exit immediately when encountering an error

PDF_FILE="${1:-}"

if [ -z "$PDF_FILE" ]; then
    echo "Usage: $0 <PDF file>"
    echo ""
    echo "Example: bash test_quick_e2e.sh test.pdf"
    exit 1
fi

if [ ! -f "$PDF_FILE" ]; then
    echo "❌ Error: File not found: $PDF_FILE"
    exit 1
fi

# Convert to absolute path
PDF_FILE=$(realpath "$PDF_FILE")
PDF_NAME=$(basename "$PDF_FILE")

echo "=========================================="
echo "🎯 hOCR optimized end-to-end testing"
echo "=========================================="
echo ""
echo "📄 PDF file: $PDF_NAME"
echo "📁 Full path: $PDF_FILE"
echo "📊 File size: $(du -h "$PDF_FILE" | cut -f1)"
echo ""

#Create temporary directory
TEMP_DIR="/tmp/hocr_test_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$TEMP_DIR"
echo "📂 Temporary directory: $TEMP_DIR"
echo ""

cd "$TEMP_DIR"

# ============================================
# Step 1: Deconstruct PDF
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[1/5] Deconstruct PDF → TIFF image"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

pdftoppm -tiff -tiffcompression lzw -r 300 "$PDF_FILE" page

IMAGE_COUNT=$(ls page-*.tif 2>/dev/null | wc -l)

if [ $IMAGE_COUNT -eq 0 ]; then
    echo ""
    echo "❌ Error: No image files were generated"
    echo ""
    echo "Please check:"
    echo "1. Is the PDF file normal?"
    echo "2. Is pdftoppm installed: sudo apt install poppler-utils"
    exit 1
fi

FIRST_IMAGE=$(ls page-*.tif | head -1)
IMAGE_SIZE=$(du -h "$FIRST_IMAGE" | cut -f1)

echo "✅ Success: $IMAGE_COUNT image files generated"
echo "Single file size: ~$IMAGE_SIZE"
echo ""

# ============================================
# Step 2: OCR recognition
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[2/5] OCR recognition → generate hOCR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

OCR_COUNT=0
for img in page-*.tif; do
    base=$(basename "$img" .tif)
    OCR_COUNT=$((OCR_COUNT + 1))
    echo -ne "\r Progress: $OCR_COUNT/$IMAGE_COUNT"
    tesseract "$img" "$base" -l eng hocr 2>/dev/null
done
echo ""

HOCR_COUNT=$(ls page-*.hocr 2>/dev/null | wc -l)
if [ $HOCR_COUNT -eq 0 ]; then
    echo ""
    echo "❌ Error: OCR did not generate any hOCR files"
    echo ""
    echo "Please check:"
    echo "1. Is tesseract installed: sudo apt install tesseract-ocr"
    echo "2. Is the English language pack installed: sudo apt install tesseract-ocr-eng"
    exit 1
fi

echo "✅ Success: $HOCR_COUNT hOCR files generated"
echo ""

# ============================================
# Step 3: Merge hOCR
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[3/5] Merge hOCR files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 << 'PYTHON_MERGE'
import glob
import re
import sys

files = sorted(glob.glob('page-*.hocr'))
if not files:
    print("❌ Error: hOCR file not found")
    sys.exit(1)

print(f"Merge {len(files)} files...")

# Read the first file as template
with open(files[0], 'r', encoding='utf-8') as f:
    template = f.read()

# Separate head and tail
body_match = re.search(r'<body>(.*?)</body>', template, re.DOTALL)
if not body_match:
    print("❌ Error: Unable to parse hOCR format")
    sys.exit(1)

header = template[:body_match.start(1)]
footer = template[body_match.end(1):]

# Collect all pages
pages = []
for hocr_file in files:
    with open(hocr_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    match = re.search(r'<body>(.*?)</body>', content, re.DOTALL)
    if match:
        pages.append(match.group(1))

# Merge and write
merged = header + '\n'.join(pages) + footer
with open('combined.hocr', 'w', encoding='utf-8') as f:
    f.write(merged)

print(f"✅ 成功: combined.hocr ({len(merged)/1024/1024:.1f} MB)")
PYTHON_MERGE

if [ ! -f "combined.hocr" ]; then
    echo "❌ Error: Merge failed"
    exit 1
fi

ORIGINAL_HOCR_SIZE=$(du -h combined.hocr | cut -f1)
echo ""

# ============================================
# Step 4: Optimize hOCR
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[4/5] Optimize hOCR (remove ocrx_word tag)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 << 'PYTHON_OPTIMIZE'
import re

with open('combined.hocr', 'r', encoding='utf-8') as f:
    content = f.read()

original_size = len(content)

# Delete all ocrx_word tags
optimized = re.sub(
    r"<span class='ocrx_word'[^>]*>.*?</span>",
    '',
    content,
    flags=re.DOTALL
)

optimized_size = len(optimized)
reduction = (1 - optimized_size / original_size) * 100

with open('combined_no_words.hocr', 'w', encoding='utf-8') as f:
    f.write(optimized)

print(f"Original size: {original_size/1024/1024:.2f} MB")
print(f" After optimization: {optimized_size/1024/1024:.2f} MB")
print(f" Reduction: {reduction:.1f}%")
print(f"✅ Success: combined_no_words.hocr")
PYTHON_OPTIMIZE

echo ""

# ============================================
# Step 5: Generate PDF
# ============================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[5/5] Generate test PDF"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: Raw hOCR
echo "[1/2] Use raw hOCR..."
if recode_pdf --from-imagestack "page-*.tif" \
    --hocr-file combined.hocr \
    --dpi 300 \
    --bg-downsample 2 \
    -J grok \
    -o test_original.pdf 2>&1 | grep -i "error\|traceback" ; then
    echo " ⚠️ An error occurred while generating the original version (continue)"
fi

if [ -f "test_original.pdf" ]; then
    echo "      ✅ test_original.pdf ($(du -h test_original.pdf | cut -f1))"
else
    echo " ⚠️ not generated (may have errors)"
fi
echo ""

# Test 2: Optimize hOCR
echo "[2/2] Use optimized hOCR (no_words)..."
if recode_pdf --from-imagestack "page-*.tif" \
    --hocr-file combined_no_words.hocr \
    --dpi 300 \
    --bg-downsample 2 \
    -J grok \
    -o test_no_words.pdf 2>&1 | grep -i "error\|traceback" ; then
    echo " ❌ Optimized version generation failed"
    exit 1
fi

if [ -f "test_no_words.pdf" ]; then
    echo "      ✅ test_no_words.pdf ($(du -h test_no_words.pdf | cut -f1))"
else
    echo " ❌ not generated"
    exit 1
fi

echo ""
echo "=========================================="
echo "📊 test results"
echo "=========================================="
echo ""

# Detailed list
echo "hOCR file:"
ls -lh combined*.hocr | awk '{printf "  %-30s %8s\n", $9, $5}'

echo ""
echo "PDF file:"
ls -lh test_*.pdf | awk '{printf "  %-30s %8s\n", $9, $5}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Calculate savings
if [ -f "test_original.pdf" ] && [ -f "test_no_words.pdf" ]; then
    ORIG_SIZE=$(stat -c%s test_original.pdf 2>/dev/null || stat -f%z test_original.pdf)
    OPT_SIZE=$(stat -c%s test_no_words.pdf 2>/dev/null || stat -f%z test_no_words.pdf)
    DIFF=$((ORIG_SIZE - OPT_SIZE))
    
    if [ $DIFF -gt 0 ]; then
        DIFF_MB=$(echo "scale=2; $DIFF / 1024 / 1024" | bc)
        PCT=$(echo "scale=1; $DIFF * 100 / $ORIG_SIZE" | bc)
        echo "💾 Save space: ${DIFF_MB} MB (${PCT}%)"
    elif [ $DIFF -lt 0 ]; then
        DIFF_MB=$(echo "scale=2; -$DIFF / 1024 / 1024" | bc)
        echo "⚠️ After optimization, it increased to ${DIFF_MB} MB"
    else
        echo "📊 Basically the same size"
    fi
fi

echo ""
echo "📁 All file locations:"
echo "   $TEMP_DIR"
echo ""
echo "✅ Test completed!"
echo ""
echo "Next:"
echo "1. Check PDF quality: cd $TEMP_DIR"
echo "2. Copy to Windows: cp test_*.pdf /mnt/c/Users/..."
echo "3. Test searchability (expected: original searchable, optimized not searchable)"
