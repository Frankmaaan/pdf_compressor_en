#!/bin/bash
# Simplified version of the test script - quick verification no_words hOCR

echo "=== hOCR Optimization Quick Test ==="
echo ""
echo "⚠️ Please make sure before use:"
echo "1. The current directory contains page-*.tif image stack"
echo " (usually in the temporary directory of the compression task, such as /tmp/tmpXXXXXX)"
echo "2. Run in WSL/Ubuntu environment"
echo "3. ocrmypdf-recode installed"
echo ""
echo "💡 Tip: If there is no image stack yet, please check HOW_TO_GET_TEST_FILES.md"
echo ""

# Check if there is an image file
if ! ls page-*.tif 1> /dev/null 2>&1; then
    echo "❌ Error: There is no page-*.tif file in the current directory"
    echo ""
    echo "Please first:"
    echo "1. Run the compression task: python main.py -i testpdf156.pdf -o output -t 2 --keep-temp-on-failure"
    echo "2. Enter the temporary directory: cd /tmp/tmpXXXXXX"
    echo "3. Run this script again"
    echo ""
    echo "For detailed instructions, please view: test_hocr/HOW_TO_GET_TEST_FILES.md"
    exit 1
fi

IMAGE_COUNT=$(ls page-*.tif 2>/dev/null | wc -l)
echo "✅ $IMAGE_COUNT image files found"
echo ""

# Set path - automatically detects multiple possible locations
POSSIBLE_PATHS=(
    "/mnt/c/Users/quying/Projects/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr"
    "$HOME/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr"
    "~/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr"
    "./combined_no_words.hocr"
)

HOCR_FILE=""
for path in "${POSSIBLE_PATHS[@]}"; do
    expanded_path=$(eval echo "$path")
    if [ -f "$expanded_path" ]; then
        HOCR_FILE="$expanded_path"
        break
    fi
done

IMAGE_PATTERN="page-*.tif"
OUTPUT_PDF="test_no_words.pdf"

# Check hOCR file
if [ -z "$HOCR_FILE" ] || [ ! -f "$HOCR_FILE" ]; then
    echo "❌ The optimized hOCR file cannot be found"
    echo ""
    echo "Tried path:"
    for path in "${POSSIBLE_PATHS[@]}"; do
        echo "  - $path"
    done
    echo ""
    echo "Solution:"
    echo "1. Copy combined_no_words.hocr to the current directory:"
    echo "   cp ~/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr ."
    echo ""
    echo "2. Or manually specify the hOCR file path to run recode_pdf:"
    echo "   recode_pdf --from-imagestack page-*.tif \\"
    echo "       --hocr-file /path/to/combined_no_words.hocr \\"
    echo "       --dpi 72 --bg-downsample 10 -J grok \\"
    echo "       -o test_no_words.pdf"
    exit 1
fi

echo "📄 hOCR file: $(basename "$HOCR_FILE") ($(du -h "$HOCR_FILE" | cut -f1))"
echo "🖼️ Image mode: $IMAGE_PATTERN"
echo "📦 Output file: $OUTPUT_PDF"
echo ""
echo "Start generating PDF..."
echo ""

# Execute key commands
recode_pdf --from-imagestack $IMAGE_PATTERN \
    --hocr-file "$HOCR_FILE" \
    --dpi 72 \
    --bg-downsample 10 \
    -J grok \
    -o "$OUTPUT_PDF"

# Check results
if [ $? -eq 0 ] && [ -f "$OUTPUT_PDF" ]; then
    echo ""
    echo "✅ Success! PDF has been generated"
    echo "Size: $(du -h "$OUTPUT_PDF" | cut -f1)"
    echo "Location: $OUTPUT_PDF"
    echo ""
    echo "Please test:"
    echo "• Open the PDF and check whether the display is normal"
    echo "• Try searching text (Ctrl+F)"
    echo "• Try selecting and copying text"
else
    echo ""
    echo "❌ Failed! Please check the error message"
    exit 1
fi
