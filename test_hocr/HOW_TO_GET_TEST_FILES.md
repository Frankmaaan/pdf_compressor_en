# How to obtain the files required for hOCR testing

## 📋 Required documents

Two types of files are required to test hOCR optimization:

1. **Image stack** (imagestack): `page-001.tif`, `page-002.tif`, ..., `page-156.tif`
2. **Original hOCR file**: `combined.hocr` (9.05 MB)

---

## 🔧 Method 1: Obtain from compression task (recommended)

### Step 1: Run the compression task and keep the temporary files

```bash
# In WSL/Ubuntu environment
cd ~/pdf_compressor

# Run compression, keep temporary files
python main.py -i testpdf156.pdf -o output -t 2 --keep-temp-on-failure
```

**Key Parameters**:
- `--keep-temp-on-failure`: keep temporary directory even on failure
- Or modify the code to temporarily disable automatic cleaning

### Step 2: Find the temporary directory

In the output of the compression process, the temporary directory path is displayed:

```
[Information] Temporary working directory: /tmp/tmpXXXXXX
```

Or search in the log file for:

```bash
grep "temporary" logs/compression_*.log
```

### Step 3: Enter the temporary directory to view files

```bash
cd /tmp/tmpXXXXXX

# List all files
ls -lh

# You should see:
# page-001.tif
# page-002.tif
# ...
# page-156.tif
# combined.hocr ← Original hOCR file (~9 MB)
```

### Step 4: Copy the files to the project directory (optional)

```bash
# Copy original hOCR (if not already there)
cp combined.hocr /mnt/c/Users/quying/Projects/pdf_compressor/docs/testpdf156.hocr

# NOTE: Image files are large (~400-500 MB) and usually do not need to be copied
# Just test directly in the temporary directory
```

---

## 🧪 Method 2: Manually deconstruct PDF (if needed)

If the temporary directory has been cleaned, the PDF can be deconstructed manually:

### Extract images using Ghostscript

```bash
# Install ghostscript (if not installed yet)
sudo apt-get install ghostscript

# Deconstruct PDF to TIFF image
gs -dNOPAUSE -dBATCH -sDEVICE=tiff24nc -r300 \
   -sOutputFile=page-%03d.tif \
   testpdf156.pdf
```

**Description**:
- `-r300`: resolution 300 DPI
- `-sDEVICE=tiff24nc`: 24-bit color TIFF
- `-sOutputFile=page-%03d.tif`: output file name format

### Use ocrmypdf-recode to generate hOCR

```bash
# OCR all images
tesseract page-001.tif page-001 -l eng hocr
tesseract page-002.tif page-002 -l eng hocr
# ... (repeat for all pages)

# Or use a loop
for i in {001..156}; do
    tesseract page-$i.tif page-$i -l eng hocr
done

# Merge all hOCR files
# (This step is more complicated and is usually handled with a Python script)
```

**⚠️ Note**: The manual method is very cumbersome, and method 1 is highly recommended!

---

## 🎯 Test directly in the temporary directory (easiest)

**Recommended practice**: Do not copy files, test directly in the temporary directory

### Step 1: Run the compression task

```bash
python main.py -i testpdf156.pdf -o output -t 2 --keep-temp-on-failure
```

### Step 2: After compression fails, enter the temporary directory

```bash
cd /tmp/tmpXXXXXX # Use the actual path shown in the output
```

### Step 3: Test the optimized hOCR directly here

```bash
# Copy the optimized hOCR file here
cp /mnt/c/Users/quying/Projects/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr ./

# Generate PDF using original image and optimized hOCR
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined_no_words.hocr \
    --dpi 72 \
    --bg-downsample 10 \
    -J grok \
    -o test_no_words.pdf

# Check results
ls -lh test_no_words.pdf

# Compare to original hOCR version (if combined.hocr is still there)
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined.hocr \
    --dpi 72 \
    --bg-downsample 10 \
    -J grok \
    -o test_original.pdf

# Compare size
ls -lh test_*.pdf
```

---

## 📊 File size reference

**Image Stack** (page 156):
- Single TIFF file: ~2-3 MB (300 DPI)
- Total size: approx. **300-500 MB**

**hOCR file**:
- Original: 9.05 MB
- After optimization (no_words): 1.60 MB

**Generated PDF** (S7 parameters):
- Expected: 2-8 MB range

---

## 🔍 Verify that the file is correct

### Check image files

```bash
# Count the number of files
ls page-*.tif | wc -l
# Should output: 156

# Check file format
file page-001.tif
#Should output: TIFF image data, ...

# View image information
identify page-001.tif
#Should display: width x height, resolution, color depth
```

### Check hOCR files

```bash
# Check file size
ls -lh combined.hocr
# Should be about 9 MB

# Check XML format
head -20 combined.hocr
# You should see: <?xml version="1.0"...
#           <html xmlns="http://www.w3.org/1999/xhtml"...

# Count the number of pages
grep -c "ocr_page" combined.hocr
# Should output: 156
```

---

## 💡 Practical Tips

### 1. Method to retain temporary directory

**Method A**: Modify the code to temporarily disable cleaning

Edit `compressor/pipeline.py`:

```python
# Find the code that cleans the temporary directory and comment it out
# shutil.rmtree(temp_dir)
print(f"The temporary directory has been reserved: {temp_dir}")
```

**Method B**: Automatically retain on failure

The code already supports the `--keep-temp-on-failure` parameter.

### 2. Quickly locate the latest temporary directory

```bash
# Find the recently created /tmp/tmp* directory
ls -lt /tmp/ | grep tmp | head -1

# or
cd $(ls -td /tmp/tmp* | head -1)
```

### 3. Save disk space

The image file is very large, clean it up immediately after the test is completed:

```bash
# Keep only necessary files
rm page-*.tif # Delete image (if no longer needed)
# Keep hOCR and generated PDF for analysis
```

---

## ✅ READY TO CHECKLIST

Before starting the hOCR test, confirm:

- [ ] There are 156 `page-XXX.tif` files
- [ ] has the original `combined.hocr` file (~9 MB)
- [ ] Optimized hOCR file is ready
- [ ] `recode_pdf` command is available
- [ ] Sufficient disk space (at least 1 GB)

---

## 🚀 Quick test command

```bash
# One-click testing process
cd /tmp/tmpXXXXXX # your temporary directory

#Copy optimization hOCR
cp /mnt/c/Users/quying/Projects/pdf_compressor/docs/hocr_experiments/combined_no_words.hocr ./

# Generate test PDF
recode_pdf --from-imagestack page-*.tif \
    --hocr-file combined_no_words.hocr \
    --dpi 72 --bg-downsample 10 -J grok \
    -o test_no_words.pdf

# View results
ls -lh test_no_words.pdf
echo "If the PDF is generated successfully, this will be a major breakthrough!"
```

---

**Creation date**: 2025-10-19
**Applicable scenarios**: hOCR optimization test
**Key Tip**: It is easiest to test directly in the temporary directory of the compression task!
