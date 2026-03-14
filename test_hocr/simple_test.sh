#!/bin/bash
# Super simple test script - test hOCR optimization in temporary directory

echo "=== hOCR optimization test (simplified version)==="
echo ""

# Check if there is an image file
if ! ls page-*.tif 1> /dev/null 2>&1; then
    echo "❌ There is no page-*.tif file in the current directory"
    echo "Please cd to the directory containing the image first (such as /tmp/tmpXXXXXX)"
    exit 1
fi

IMAGE_COUNT=$(ls page-*.tif 2>/dev/null | wc -l)
echo "✅ $IMAGE_COUNT image files found"
echo ""

# Check if there is already optimized hOCR
if [ ! -f "combined_no_words.hocr" ]; then
    echo "📥 Optimized hOCR not found, copying from project..."
    
    # Try multiple possible source paths
    POSSIBLE_SOURCES=(
        "$HOME/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr"
        "/mnt/c/Users/quying/Projects/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr"
    )
    
    COPIED=false
    for src in "${POSSIBLE_SOURCES[@]}"; do
        if [ -f "$src" ]; then
            cp "$src" ./combined_no_words.hocr
            echo "✅ Copied: $(basename "$src")"
            COPIED=true
            break
        fi
    done
    
    if [ "$COPIED" = false ]; then
        echo ""
        echo "❌ Unable to find optimized hOCR file"
        echo ""
        echo "Please manually copy the file to the current directory:"
        echo "  cp /path/to/combined_no_words.hocr ."
        echo ""
        echo "Or use combined.hocr from the original temporary directory:"
        echo "  recode_pdf --from-imagestack page-*.tif \\"
        echo "      --hocr-file combined.hocr \\"
        echo "      --dpi 72 --bg-downsample 10 -J grok \\"
        echo "      -o test_original.pdf"
        exit 1
    fi
fi

echo "📄 hOCR file: combined_no_words.hocr ($(du -h combined_no_words.hocr | cut -f1))"
echo "🖼️ Number of images: $IMAGE_COUNT"
echo ""
echo "Start generating PDF..."
echo ""

# Execute recode_pdf
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined_no_words.hocr \
    --dpi 72 \
    --bg-downsample 10 \
    -J grok \
    -o test_no_words.pdf

# Check results
if [ $? -eq 0 ] && [ -f "test_no_words.pdf" ]; then
    echo ""
    echo "=========================================="
    echo "✅ Success! PDF generated"
    echo "=========================================="
    echo "File: test_no_words.pdf"
    echo "Size: $(du -h test_no_words.pdf | cut -f1)"
    echo ""
    echo "Next step:"
    echo "1. Check PDF quality: open test_no_words.pdf"
    echo "2. Compare to original version (if combined.hocr is available):"
    echo "   recode_pdf --from-imagestack page-*.tif \\"
    echo "       --hocr-file combined.hocr \\"
    echo "       --dpi 72 --bg-downsample 10 -J grok \\"
    echo "       -o test_original.pdf"
    echo "3. Compare file sizes:"
    echo "   ls -lh test_*.pdf"
else
    echo ""
    echo "❌ PDF generation failed"
    echo "Please check the error message above"
    exit 1
fi
