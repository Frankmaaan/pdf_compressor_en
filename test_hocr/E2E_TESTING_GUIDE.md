# End-to-end testing guide - directly using PDF files

## 🎯 Test purpose

Perform complete hOCR optimization testing directly from PDF files without manual manipulation of intermediate files.

---

## 📋 Preparation

### 1. Upload the test script to the remote host

```bash
# On the remote Ubuntu/WSL host
cd ~/pdf_compressor

# Make sure the script has execution permissions
chmod +x test_hocr/test_pdf_e2e.sh
chmod +x test_hocr/test_quick_e2e.sh
```

### 2. Prepare test PDF

Upload a test PDF file to the remote host, or use an existing PDF:

```bash
# Example: Upload files
scp testpdf156.pdf user@remote-host:~/

# Or find an existing PDF on the remote host
ls ~/testpdf*.pdf
```

---

## 🚀 Run tests

### Method 1: Quick test (recommended)

**The easiest and fastest way**

```bash
# Execute on the remote host
cd ~/pdf_compressor
bash test_hocr/test_quick_e2e.sh ~/testpdf156.pdf
```

**Example output**:
```
🎯 Quick hOCR optimization test
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PDF: testpdf156.pdf (12.3M)

[1/4] Deconstruct PDF...
✅ 156 pages
[2/4] OCR recognition...
[3/4] Optimize hOCR (delete ocrx_word)...
✅ Optimization: 9.1MB → 1.6MB (-82.4%)
[4/4] Generate PDF...
Original hOCR...
Optimize hOCR...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
combined.hocr             9.1M
combined_no_words.hocr    1.6M
test_original.pdf         10.2M
test_no_words.pdf         2.8M

📁 Location: /tmp/hocr_quick_test_12345

✅ Success! Saved 7.4MB (72.5%)
```

**Time**: ~10-15 minutes (depends on number of pages and CPU)

---

### Method 2: Detailed testing

**Contains more detailed progress information and analysis**

```bash
bash test_hocr/test_pdf_e2e.sh ~/testpdf156.pdf
```

**Optional: Specify temporary directory**

```bash
bash test_hocr/test_pdf_e2e.sh ~/testpdf156.pdf /tmp/my_test
```

**Output**: Contains complete step instructions and detailed statistics

---

## 📊 View results

### 1. Check the generated files

```bash
# Enter the test directory
cd /tmp/hocr_quick_test_* # use actual directory name

# List all files
ls -lh

# should see:
# - page-*.tif (image file)
# - page-*.hocr (single page hOCR)
# - combined.hocr (original combined hOCR, ~9MB)
# - combined_no_words.hocr (optimized hOCR, ~1.6MB)
# - test_original.pdf (generated using original hOCR)
# - test_no_words.pdf (generated using optimized hOCR)
```

### 2. Compare file sizes

```bash
# Detailed comparison
echo "hOCR file:"
ls -lh combined*.hocr

echo ""
echo "PDF file:"
ls -lh test_*.pdf
```

### 3. View PDF information

```bash
# View PDF metadata
pdfinfo test_original.pdf
pdfinfo test_no_words.pdf

# Check page count
grep -c "Pages:" test_*.pdf
```

---

## 🧪 Verification test

### 1. Copy PDF to Windows

```bash
# Copy to shared directory (adjust according to your environment)
cp test_*.pdf /mnt/c/Users/quying/Desktop/

# Or use scp
scp test_*.pdf user@windows-host:/path/to/destination/
```

### 2. Open PDF in Windows

- Open `test_original.pdf` and `test_no_words.pdf`
- Compare display quality
- Test searchability (Ctrl+F)

### 3. Verification Checklist

- [ ] PDF can be opened normally
- [ ] page display is clear
- [ ] Image quality is acceptable
- [ ] Text formatting is correct
- [ ] File size significantly reduced

**Expected results**:
- ✅ `test_original.pdf` is searchable (text can be found)
- ⚠️ `test_no_words.pdf` is not searchable (this is expected since word tags were removed)
- ✅ The visual quality of both PDFs should be exactly the same
- ✅ `test_no_words.pdf` should be 20-70% smaller

---

## 📈 Analysis of expected results

### Sign of success

**hOCR Optimization**:
- Original hOCR: 9.0-9.5 MB
- Optimized hOCR: 1.5-2.0 MB
- Reduction ratio: 80-85% ✅

**PDF size** (using DPI=300, BG-Downsample=2):
- Original version: 8-12 MB
- Optimized version: 2-8 MB
- Space saving: 20-70% ✅

### If the savings aren't obvious...

Possible reasons:
1. PDF itself is very small (hOCR ratio is low)
2. Image part dominates (hOCR has limited impact)
3. Using high DPI (large image footprint)

**Solution**:
- Try more aggressive parameters (DPI=72, BG-Downsample=10)
- Test other optimization strategies (no_lines, minimal)

---

## 🔧 Test different parameters

### Test S7 radical parameters

```bash
# Enter the test directory
cd /tmp/hocr_quick_test_*

# Regenerate using S7 parameters
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined_no_words.hocr \
    --dpi 72 \
    --bg-downsample 10 \
    -J grok \
    -o test_no_words_s7.pdf

# Check the size
ls -lh test_no_words*.pdf
```

### Test other optimization strategies

```bash
# Generate no_lines version (retain ocrx_word, delete ocr_line)
python3 -c "
import re
with open('combined.hocr', 'r') as f:
    content = f.read()
optimized = re.sub(r\"<span class='ocr_line'[^>]*>.*?</span>\", '', content, flags=re.DOTALL)
with open('combined_no_lines.hocr', 'w') as f:
    f.write(optimized)
"

# test generation
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined_no_lines.hocr \
    --dpi 300 --bg-downsample 2 -J grok \
    -o test_no_lines.pdf
```

---

## ❓ FAQ

### Q1: What should I do if the script execution is very slow?

**A**: This is normal. Mainly time-consuming:
- Deconstruct PDF: ~30 seconds
- OCR recognition: ~5-10 minutes (depends on the number of pages)
- Generate PDF: ~1-2 minutes

For a 156 page PDF, the total time is approximately **10-15 minutes**.

### Q2: What should I do if OCR fails?

**A**: Check tesseract and language packs:
```bash
tesseract --version
tesseract --list-langs

# If eng is not available, install it
sudo apt install tesseract-ocr-eng
```

### Q3: What should I do if recode_pdf reports an error?

**A**: Check installation:
```bash
recode_pdf --version

# If not installed
pip install archive-pdf-tools
# or
pipx install archive-pdf-tools
```

### Q4: Want to test a single page PDF?

**A**: Extract a single page first:
```bash
# Extract the first page
qpdf --pages test.pdf 1 -- test_1page.pdf

# Then test
bash test_hocr/test_quick_e2e.sh test_1page.pdf
```

---

## 🎯 Next step

### If the test is successful

1. **Record the results**
   ```bash
   # In the test directory
   echo "Test Date: $(date)" > RESULTS.txt
   echo "Original PDF: $(du -h ~/testpdf156.pdf | cut -f1)" >> RESULTS.txt
   echo "" >> RESULTS.txt
   ls -lh test_*.pdf combined*.hocr >> RESULTS.txt
   ```

2. **Integrate into project**
- Modify `compressor/pipeline.py` to add hOCR optimization function
- Add `--optimize-hocr` parameter
- Update documentation

3. **Release new version**
- Create v2.1.0 tag
- Update CHANGELOG
- Push to GitHub

### If the test fails

1. **Collect error information**
   ```bash
   # Save complete output
   bash test_hocr/test_quick_e2e.sh test.pdf 2>&1 | tee test_error.log
   ```

2. **Try alternatives**
- Test `no_lines` strategy
- Test `minimal` strategy
- Study the recode_pdf document

3. **Report a problem**
- Create an issue in the project
- Attach error log and environment information

---

## 📝 Test record template

```markdown
# hOCR Optimize test records

## Test environment
- Date: 2025-10-19
- Host: Ubuntu 22.04
- PDF: testpdf156.pdf (156 pages, 12.3 MB)

## Test results

### hOCR file
- Original: 9.1 MB
- Optimized: 1.6 MB
- Reduction: 82.4%

### PDF file
- Original parameters (DPI=300, BG=2): 10.2 MB
- Optimized parameters (DPI=300, BG=2): 2.8 MB
- Savings: 7.4 MB (72.5%)

### S7 aggressive parameters (DPI=72, BG=10)
- Optimized version: 1.2 MB
- Savings: 90%

## Quality Assessment
- [ ] Display Quality: Excellent
- [ ] Searchability: lost (expected)
- [ ] Visual integrity: Complete

## Conclusion
✅ Test successful! It is recommended to integrate into the project.
```

---

**Creation date**: 2025-10-19
**Applicable scenarios**: Remote host end-to-end testing
**Test script**: test_quick_e2e.sh, test_pdf_e2e.sh
**Estimated time**: 10-15 minutes (156 pages PDF)
