# hOCR Optimization Testing - Complete Process Guide

## 🎯 Test target

Verify that the hOCR file after removing the `ocrx_word` tag can successfully generate a usable PDF.

**If successful**: hOCR can be reduced from 9.05 MB to 1.60 MB, saving 7.46 MB!

---

## 📋 Overview of testing process

```
1. Run compression task → generate image stack and raw hOCR
                     ↓
2. Analyze original hOCR → generate 4 optimized versions
                     ↓
3. Use optimized hOCR → test PDF generation
                     ↓
4. Validate results → Check size, quality, searchability
```

---

## 🔧 Detailed steps

### Step 1: Get test files

#### Method A: Obtain from compression task (recommended)

```bash
#Run in WSL/Ubuntu
cd ~/pdf_compressor

#Run the compression task and keep temporary files
python main.py -i testpdf156.pdf -o output -t 2 --keep-temp-on-failure
```

**Example output**:
```
[Information] Temporary working directory: /tmp/tmp1a2b3c4d
[Execute] Deconstruct PDF...
[Execute] OCR recognition...
...
[Failure] Failed to reach goal...
[Reserved] Temporary directory has been reserved: /tmp/tmp1a2b3c4d
```

**Enter temporary directory**:
```bash
cd /tmp/tmp1a2b3c4d

# View files
ls -lh
# should see:
# page-001.tif, page-002.tif, ..., page-156.tif
# combined.hocr (approx. 9 MB)
```

---

### Step 2: Analyze the hOCR file (if you haven’t done so already)

```bash
# Run in Windows or WSL
python test_hocr/hocr_analyzer.py docs/testpdf156.hocr
```

**Output**:
```
========================================
hOCR file analysis report
========================================

File: docs/testpdf156.hocr
Size: 9.05 MB
Total number of lines: 101,812

Structural statistics:
- ocr_page: 156
- ocr_carea: 1,356
- ocr_par: 2,063
- ocr_line: 5,107
- ocrx_word: 77,971 ← Key!

Content proportion:
- Text content: 269.69 KB (2.9%)
- bbox coordinates: 1.96 MB (21.7%)
- Others: 6.83 MB (75.4%) ← Tag structure

========================================
Generate optimized version
========================================

✅ Empty text version: 8.88 MB (-1.8%)
✅ Minimized version: 8.49 MB (-6.2%)
✅ No word version: 1.60 MB (-82.4%) ← Focus test!
✅ No line version: 7.91 MB (-12.6%)

All files are saved to: docs/hocr_experiments/
```

---

### Step 3: Test PDF generation

#### Method A: Use a quick test script

```bash
# Enter the temporary directory (the place containing page-*.tif)
cd /tmp/tmp1a2b3c4d

#Run test script
bash /mnt/c/Users/quying/Projects/pdf_compressor/test_hocr/quick_test.sh
```

#### Method B: Manual testing

```bash
# In the temporary directory
cd /tmp/tmp1a2b3c4d

# Copy optimized hOCR
cp /mnt/c/Users/quying/Projects/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr ./

# Generate PDF (using S7 parameters)
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined_no_words.hocr \
    --dpi 72 \
    --bg-downsample 10 \
    -J grok \
    -o test_no_words.pdf

# Check results
ls -lh test_no_words.pdf
```

**Expected Output**:
```
# if successful
-rw-r--r-- 1 user user 2.5M Oct 19 10:30 test_no_words.pdf
✅ PDF generated successfully!

# if failed
Error: [error message for recode_pdf]
❌ Need to try other strategies
```

---

### Step 4: Verify and compare

#### 4.1 Basic inspection

```bash
# View PDF information
pdfinfo test_no_words.pdf

# should display:
# Pages: 156
# Page size: XXX x YYY pts
# File size: X MB
# ...
```

#### 4.2 Generate control group (using original hOCR)

```bash
# If the original combined.hocr is still there
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined.hocr \
    --dpi 72 \
    --bg-downsample 10 \
    -J grok \
    -o test_original.pdf

# Compare size
ls -lh test_*.pdf
```

**Comparison example**:
```
-rw-r--r-- 1 user user 10.2M test_original.pdf ← original hOCR
-rw-r--r-- 1 user user 2.8M test_no_words.pdf ← Optimize hOCR
                        ^^^^
                     Save 7.4 MB!
```

#### 4.3 Quality Check

```bash
# Open PDF in Windows
explorer.exe test_no_words.pdf

# Or copy to Windows
cp test_no_words.pdf /mnt/c/Users/quying/Desktop/
```

**Manual Check**:
- [ ] The page displays normally
- [ ] Image sharpness is acceptable
- [ ] Text formatting is correct
- [ ] No corruption or garbled characters

**Searchability Test** (expected to fail):
- [ ] Press Ctrl+F to search for text → ❌ Unable to search (expected)
- [ ] Trying to select text → ❌ Unable to select (expected)

**Note**: There is a loss of searchability with the wordless version, which is an expected trade-off.

---

## 📊 Result record

### Test result table

| hOCR Version | hOCR Size | PDF Generation | PDF Size | Savings | Searchable | Quality |
|-----------|-----------|----------|----------|--------|--------|------|
| Original | 9.05 MB | ✓ | ? MB | - | ✓ | ✓ |
| no_words | 1.60 MB | ? | ? MB | ? MB | ✗ | ? |
| no_lines | 7.91 MB | ? | ? MB | ? MB | ? | ? |
| minimal | 8.49 MB | ? | ? MB | ? MB | ? | ? |

Fill in the actual test data...

---

## ✅ Success Criteria

A successful test requires:

1. **PDF generated successfully**
- `recode_pdf` exits normally
- The generated PDF file exists

2. **Reasonable file size**
- Smaller than original hOCR version (expected 7+ MB reduction)
- Within acceptable range (2-8 MB)

3. **Visual quality acceptable**
- The page displays normally
- No obvious damage or distortion

4. **Functional loss acceptable**
- Loss of searchability (known and acceptable)
- Full display functionality

---

## 🎉 If the test is successful

### Act now

1. **Record detailed data**
- PDF file size
- Generation time
- Quality assessment

2. **Update documentation**
- Record the results in `docs/hOCR Experiment_Real Data Analysis.md`
- Update README.md

3. **Prepare for integration**
- Design `optimize_hocr()` function
- added to `pipeline.py`
- Create `--optimize-hocr` parameter

4. **Release new version**
- Tag v2.1.0
-Write CHANGELOG
- Push to GitHub

### Potential Impact

**For the 156 page PDF project**:
- Currently: S7 generates 4-5 MB (substandard)
- After optimization: S7 may generate under 2 MB (success!)

**To the project as a whole**:
- The success rate of extreme compression is greatly improved
- Possibility to use milder parameters (preserving quality)
- Significantly reduces processing time

---

## ❌ If the test fails

### Error analysis

**Common failure situations**:

1. **recode_pdf error**
   ```
   Error: hOCR file format is incorrect
   ```
   → Note that recode_pdf requires the ocrx_word tag

2. **PDF generated but corrupted**
   ```
   PDF cannot be opened or displays abnormally
   ```
   → The description structure is incomplete

3. **PDF too large**
   ```
   File size is not reduced
   ```
   → Explain that hOCR size is not a bottleneck

### Alternatives

**Testing by priority**:

#### Alternative 1: no_lines version (-12.6%)

```bash
recode_pdf --from-imagestack page-*.tif \
    --hocr-file /mnt/c/.../combined_no_lines.hocr \
    --dpi 72 --bg-downsample 10 -J grok \
    -o test_no_lines.pdf
```

**Advantage**: Keep ocrx_word, only delete ocr_line

#### Alternative 2: minimal version (-6.2%)

```bash
recode_pdf --from-imagestack page-*.tif \
    --hocr-file /mnt/c/.../combined_minimal.hocr \
    --dpi 72 --bg-downsample 10 -J grok \
    -o test_minimal.pdf
```

**Advantages**: Keep all tags and only simplify attributes

#### Alternative 3: Research recode_pdf requirements

- View ocrmypdf-recode source code
- Determine minimum required tags
- Design the minimum feasible hOCR structure

---

## 🔍 Troubleshooting

### Problem 1: Image file not found

```
❌ Error: page-*.tif files not found
```

**Solution**:
- Make sure you are in the correct directory (temporary directory)
- Check file naming format
- View `HOW_TO_GET_TEST_FILES.md`

### Problem 2: hOCR file not found

```
❌ Optimized hOCR file not found
```

**solve**:
```bash
# Run the analysis tool first
python test_hocr/hocr_analyzer.py docs/testpdf156.hocr

# Confirm that the file exists
ls -lh docs/hocr_experiments/combined_no_words.hocr
```

### Problem 3: recode_pdf is not installed

```
bash: recode_pdf: command not found
```

**solve**:
```bash
# Install ocrmypdf-recode
pip install ocrmypdf-recode

# or
sudo apt-get install ocrmypdf-recode
```

---

## 📝 Test Checklist

Before starting the test:
- [ ] There are 156 page-*.tif files
- [ ] has original combined.hocr (9.05 MB)
- [ ] Optimized version generated (1.60 MB)
- [ ] recode_pdf command available
- [ ] Sufficient disk space (1+ GB)

Execute the test:
- [ ] Run quick_test.sh or manual command
- [ ] PDF generated successfully
- [ ] Record file size
- [ ] Check visual quality
- [ ] Test functionality (searchability)

Record the result:
- [ ] Fill out the test results form
- [ ] Take a screenshot or save a sample page
- [ ] Update documentation
- [ ] commit Git record

---

## 🚀 Quick command reference

```bash
# 1. Run the compression task
python main.py -i testpdf156.pdf -o output -t 2 --keep-temp-on-failure

# 2. Enter the temporary directory
cd /tmp/tmpXXXXXX

# 3. Quick test
bash /mnt/c/Users/quying/Projects/pdf_compressor/test_hocr/quick_test.sh

# 4. Manual testing (if needed)
cp /mnt/c/.../combined_no_words.hocr ./
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined_no_words.hocr \
    --dpi 72 --bg-downsample 10 -J grok \
    -o test_no_words.pdf

# 5. View results
ls -lh test_no_words.pdf
pdfinfo test_no_words.pdf
```

---

**Creation date**: 2025-10-19
**Goal**: Validate feasibility of 82.4% hOCR reduction
**Key file**: combined_no_words.hocr (1.60 MB)
**Expected Impact**: 🌟🌟🌟 Breakthrough improvements (if successful)
