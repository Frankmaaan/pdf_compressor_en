#!/bin/bash
# hOCR Optimization - PDF generation test script
# Test whether hOCR can generate PDF normally after deleting the ocrx_word tag

set -e # Exit immediately when encountering an error

echo "=========================================="
echo "hOCR optimized PDF generation test"
echo "Test goal: verify whether the no_words version can generate PDF"
echo "=========================================="

# 1. Check necessary files
echo ""
echo "[1/5] Check test files..."
if [ ! -f "docs/hocr_experiments/combined_no_words.hocr" ]; then
    echo "❌ Error: combined_no_words.hocr not found"
    exit 1
fi
echo "✅ hOCR file ready ($(du -h docs/hocr_experiments/combined_no_words.hocr | cut -f1))"

# 2. Check the original image stack
echo ""
echo "[2/5] Check original image stack..."
# Here you need to provide the original page-*.tif file path
# Assume they are in some temporary or test directory
if [ -z "$IMAGE_DIR" ]; then
    echo "⚠️ warning: IMAGE_DIR environment variable not set"
    echo "Please use: IMAGE_DIR=/path/to/images ./test_no_words_pdf.sh"
    exit 1
fi

if [ ! -d "$IMAGE_DIR" ]; then
    echo "❌ Error: Image directory does not exist: $IMAGE_DIR"
    exit 1
fi

IMAGE_COUNT=$(ls "$IMAGE_DIR"/page-*.tif 2>/dev/null | wc -l)
if [ "$IMAGE_COUNT" -eq 0 ]; then
    echo "❌ Error: page-*.tif files not found in $IMAGE_DIR"
    exit 1
fi
echo "✅ $IMAGE_COUNT image files found"

# 3. Create output directory
echo ""
echo "[3/5] Prepare test environment..."
TEST_DIR="docs/hocr_experiments/pdf_test"
mkdir -p "$TEST_DIR"
echo "✅ Test directory: $TEST_DIR"

# 4. Run recode_pdf (key test)
echo ""
echo "[4/5] Run recode_pdf (using no_words hOCR)..."
echo "Command: recode_pdf --from-imagestack $IMAGE_DIR/page-*.tif \\"
echo "                  --hocr-file docs/hocr_experiments/combined_no_words.hocr \\"
echo "                  --dpi 72 \\"
echo "                  --bg-downsample 10 \\"
echo "                  -J grok \\"
echo "                  -o $TEST_DIR/test_no_words.pdf"
echo ""

START_TIME=$(date +%s)
recode_pdf --from-imagestack "$IMAGE_DIR"/page-*.tif \
    --hocr-file docs/hocr_experiments/combined_no_words.hocr \
    --dpi 72 \
    --bg-downsample 10 \
    -J grok \
    -o "$TEST_DIR/test_no_words.pdf"
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
if [ -f "$TEST_DIR/test_no_words.pdf" ]; then
    echo "✅ PDF generated successfully!"
    echo "Time taken: ${ELAPSED} seconds"
else
    echo "❌ PDF generation failed"
    exit 1
fi

# 5. Analysis results
echo ""
echo "[5/5] Test result analysis..."
PDF_SIZE=$(du -h "$TEST_DIR/test_no_words.pdf" | cut -f1)
PDF_SIZE_MB=$(du -m "$TEST_DIR/test_no_words.pdf" | cut -f1)
echo "PDF size: $PDF_SIZE (${PDF_SIZE_MB}MB)"

# If original PDF exists (using full hOCR), compare
if [ -n "$ORIGINAL_PDF" ] && [ -f "$ORIGINAL_PDF" ]; then
    ORIGINAL_SIZE_MB=$(du -m "$ORIGINAL_PDF" | cut -f1)
    SAVED_MB=$((ORIGINAL_SIZE_MB - PDF_SIZE_MB))
    SAVED_PERCENT=$((SAVED_MB * 100 / ORIGINAL_SIZE_MB))
    
    echo ""
    echo "=========================================="
    echo "Comparative analysis"
    echo "=========================================="
    echo "Original PDF (full hOCR): ${ORIGINAL_SIZE_MB}MB"
    echo "Optimize PDF (no_words): ${PDF_SIZE_MB}MB"
    echo "Save space: ${SAVED_MB}MB (${SAVED_PERCENT}%)"
fi

echo ""
echo "=========================================="
echo "✅ Test completed"
echo "=========================================="
echo "Output file: $TEST_DIR/test_no_words.pdf"
echo ""
echo "Next step:"
echo "1. Open PDF to check searchability"
echo "2. Test text selection and copy functions"
echo "3. If successful, prepare to be integrated into pipeline.py"
