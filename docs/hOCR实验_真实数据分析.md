# hOCR optimization experiment - real data analysis report

## 📊 Experimental data

### File information
- **Test file**: testpdf156.hocr
- **Original size**: 9.05 MB
- **Total Number of Rows**: 101,812 rows
- **Number of pages**: 156 pages

### Structural Statistics
| Element type | Quantity | Description |
|---------|------|------|
| ocr_page | 156 | one per page |
| ocr_carea | 1,356 | Content areas, average 8.7 per page |
| ocr_par | 2,063 | Paragraphs, average 13.2 per page |
| ocr_line | 5,107 | Lines of text, average 32.7 per page |
| **ocrx_word** | **77,971** | **Words/phrases, average 500 per page** |

### Content proportion analysis
| Components | Size | Proportion | Remarks |
|------|------|------|------|
| Text content | 269.69 KB | 2.9% | ❌ Much lower than expected |
| bbox coordinates | 1.96 MB | 21.7% | 🔴 Largest single component |
| Other | 6.83 MB | 75.4% | **Tag structure itself** |

---

## 🎯 Optimize experimental results

### Complete comparison table

| Optimization strategy | File size | Reduction amount | Reduction rate | Evaluation |
|---------|---------|--------|--------|------|
| **Original** | 9.05 MB | - | - | Benchmark |
| Empty text | 8.88 MB | 0.17 MB | 1.8% | ❌ Very poor performance |
| Minimize | 8.49 MB | 0.56 MB | 6.2% | ⚠️ Limited effect |
| **No Words** | **1.60 MB** | **7.46 MB** | **82.4%** | ✅ **Amazing Effects** |
| No lines of text | 7.91 MB | 1.14 MB | 12.6% | ⚠️ Medium effect |

---

## 🔥 Key findings

### 1. Theoretical expectations vs actual results

**Expected** (based on sample files):
- Text content accounts for 30-50%
- Empty text optimization can reduce 30-50%

**Actual** (real document):
- Text content only accounts for **2.9%** ❌
- Empty text optimization only reduces **1.8%** ❌

**Cause analysis**:
- Huge number of English words (77,971)
- But each word is short (3-4 bytes on average)
- The text ratio of sample files is seriously overestimated

### 2. The real bottleneck

**Not the text content, but the tag structure itself! **

```
77,971 ocrx_word tags = main component of 9.05 MB

Each tag averages about 100 bytes:
- <span class='ocrx_word' id='word_1_1' title='bbox 792 118 1608 236; x_wconf 85'>
- Text (3-6 bytes)
- </span>

After deletion:
9.05 MB → 1.60 MB (82.4% reduction)
```

### 3. The amazing effect of the "no word" strategy

- **9.05 MB → 1.60 MB**
- **7.46 MB less (82.4%)**
- **Far beyond the most optimistic estimates (6.8 MB)**

This is a groundbreaking discovery! 🎉

---

## ⚠️ Key questions

### Does recode_pdf require the ocrx_word tag?

**Test Matrix**:

| hOCR Version | Size | PDF Generation? | PDF Size? | Availability |
|-----------|------|-----------|-----------|--------|
| Original | 9.05 MB | ? | ? | Benchmark |
| Empty text | 8.88 MB | ? | ? | Low yield |
| Minimize | 8.49 MB | ? | ? | Low Yield |
| **No words** | **1.60 MB** | **?** | **?** | **High Yield** |
| No lines of text | 7.91 MB | ? | ? | Medium yield |

**Questions that must be verified**:
1. ✅ Can hOCR successfully generate PDF without words?
2. ✅ Is the size of the generated PDF reduced?
3. ✅ Is the visual quality of PDF affected?
4. ✅ Is the execution time of recode_pdf reasonable?

---

## 🧪 Next test plan

### Step 1: Prepare test environment

```bash
# In WSL/Ubuntu environment
cd ~/pdf_compressor

# Copy the optimized hOCR file
cp docs/hocr_experiments/combined_no_words.hocr test_no_words.hocr
```

### Step 2: Generate PDF using raw hOCR (baseline)

```bash
# Assume the image file is in /tmp/tmpj9meff1r/
cd /tmp/tmpj9meff1r/

# Use original hOCR
recode_pdf --from-imagestack page-*.tif \
           --hocr-file combined.hocr \
           --dpi 72 --bg-downsample 10 \
           --mask-compression jbig2 -J grok \
           -o test_original.pdf

# Record size and time
ls -lh test_original.pdf
```

### Step 3: Generate PDF using wordless hOCR

```bash
# Back up original hOCR
cp combined.hocr combined_original.hocr

# Use wordless version
cp ~/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr combined.hocr

# Generate PDF
recode_pdf --from-imagestack page-*.tif \
           --hocr-file combined.hocr \
           --dpi 72 --bg-downsample 10 \
           --mask-compression jbig2 -J grok \
           -o test_no_words.pdf

# Record size and time
ls -lh test_no_words.pdf
```

### Step 4: Compare results

```bash
# Size comparison
ls -lh test_*.pdf

# Calculate the reduction
# If test_no_words.pdf is smaller, record the specific MB reduction
```

### Step 5: Visual Quality Check

Use a PDF reader to open the two files and compare:
- ✅ Is the text clear?
- ✅ Is the layout normal?
- ✅ Is the image complete?

---

## 📊 Expected results

### Scenario 1: Success (optimal) ✨

```
Original hOCR (9.05 MB) → PDF: X MB
No word hOCR (1.60 MB) → PDF: (X - 7.5) MB

Actual reduction: ~7.5 MB
```

**Meaning**:
- Can take the extreme compression capabilities of the S7 solution to a new level
- Many "impossible" tasks become "possible"

### Scenario 2: Partially successful (acceptable) ⚠️

```
PDF generation successful, but reduction smaller than expected

Original hOCR (9.05 MB) → PDF: X MB
No word hOCR (1.60 MB) → PDF: (X - 2~4) MB

Actual reduction: 2-4 MB
```

**Meaning**:
- Still a significant improvement
- Can be used as a special optimization for S7

### Scenario 3: Failure (need alternative) ❌

```
recode_pdf reports an error and cannot generate PDF
Or the quality of the generated PDF is severely degraded
```

**Alternatives**:
1. Try the "no text lines" strategy (1.14 MB reduction, 12.6%)
2. Try the "minimize" strategy (reduced 0.56 MB, 6.2%)
3. Study recode_pdf’s minimum requirements for hOCR

---

## 💡 Other findings

### bbox coordinates account for a high proportion

- bbox 21.7% (1.96 MB)
- But this is required positioning information for recode_pdf
- **Cannot be removed or simplified**

### The importance of tag hierarchy

Preserved hierarchy:
```
ocr_page (156)
└── ocr_carea (1,356)
    └── ocr_par (2,063)
        └── ocr_line (5,107)
            └── [Deleted] ocrx_word (77,971)
```

After deleting the bottom ocrx_word, the 4-layer structure is still retained, which may be enough for recode_pdf.

---

## 📝 Conclusion

### Main results

1. ✅ **Real bottleneck found**: not text content, but 77,971 ocrx_word tags
2. ✅ **Find the optimal strategy**: Deleting the ocrx_word tag can reduce **82.4%** (7.46 MB)
3. ✅ **Exceeds expectations**: The actual effect far exceeds the most optimistic estimate

### Key next step

**Must be verified**: Can hOCR successfully generate PDF without words?

If successful:
- 🎉 This will be a major breakthrough for the project
- 🚀 Can be integrated immediately into S7 solutions
- 📦 Release v2.1.0 version

If it fails:
- ⚠️ Need to test other strategies
- 🔍 Study the minimum requirements for recode_pdf
- 📋 May need to retain some ocrx_word tags

---

**Creation date**: 2025-10-19
**Experimental status**: Analysis completed, waiting for PDF generation test
**Key data**: 9.05 MB → 1.60 MB (-82.4%)
**Potential Impact**: Breakthrough improvements 🌟

---

## PDF Generation Test Guide

### Method 1: Quick test (recommended)

```bash
# 1. Switch to the directory containing page-*.tif
cd /path/to/your/imagestack

# 2. Run the quick test script
bash /path/to/pdf_compressor/test_hocr/quick_test.sh
```

**Script will automatically**:
- Check no_words hOCR file (1.60 MB)
- Generate PDF using S7 parameters (DPI=72, BG-Downsample=10, JPEG2000)
- Report generation results and file size

### Method 2: Manual testing

```bash
# Execute in WSL/Ubuntu
cd /path/to/imagestack

recode_pdf --from-imagestack page-*.tif \
    --hocr-file /mnt/c/Users/quying/Projects/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr \
    --dpi 72 \
    --bg-downsample 10 \
    -J grok \
    -o test_no_words.pdf

# Check results
ls -lh test_no_words.pdf
pdfinfo test_no_words.pdf
```

### Verification Checklist

- [ ] **Command executed successfully** - Exit without error
- [ ] **PDF file generation** - the file exists and is of reasonable size
- [ ] **Searchability Test** - Open PDF, press Ctrl+F to search text
- [ ] **Text Selection Test** - Try selecting and copying text
- [ ] **Display Quality** - Check whether page rendering is normal
- [ ] **Size Comparison** - Compare file size to original hOCR version

### Expected results

#### If successful
- PDF is generated normally and searchable
- Significantly reduced file size (~7.5 MB)
- **Next step**: Integrate into pipeline.py and release v2.1.0

#### If failed
- recode_pdf reports an error or the PDF is damaged
- **Alternatives**:
1. Test no_lines (-12.6%, 7.91 MB)
2. Test minimal (-6.2%, 8.49 MB)
3. Study the minimum requirements for recode_pdf

---

**Test script**: test_hocr/quick_test.sh
**Windows path**: C:\Users\quying\Projects\pdf_compressor\docs\hocr_experiments\combined_no_words.hocr
**WSL path**: /mnt/c/Users/quying/Projects/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr
