# Fast compression mode proposal

## 📋 Background

**Problem**: The current project is slow (110 seconds/page), and the main bottleneck is OCR processing (tesseract)

**Discovery**: The speed of professional PDF compression tool reaches 0.1 seconds/page, about 1000 times faster

**Reason**: Professional tool compresses PDF internal images directly without OCR

---

## 🎯 Proposal: Add "Quick Mode"

### Core idea

**Keep existing functionality**:
- ✅ Keep the complete DAR (Deconstruction-Analysis-Reconstruction) process
- ✅ Keep OCR text layer generation
- ✅ Keep S1-S7 smart compression strategy

**New quick mode**:
- ✅ Skip OCR step (biggest bottleneck)
- ✅ Directly compress PDF internal images
- ✅ Speed increased by 5-10 times (estimated)

---

## 🔧 Technical Solution

### Option 1: Use Ghostscript to compress directly (recommended)

**Principle**: Ghostscript can directly re-encode PDF images

**Command Example**:
```bash
gs -sDEVICE=pdfwrite \
   -dCompatibilityLevel=1.4 \
   -dPDFSETTINGS=/ebook \
   -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=output.pdf input.pdf
```

**Compression Level**:
- `/screen`: 72 dpi, smallest file (similar to S7)
- `/ebook`: 150 dpi, balanced (similar to S4-S5)
- `/printer`: 300 dpi, high quality (similar to S1-S2)

**Advantages**:
- ✅ Extremely fast (5-10 seconds/document)
- ✅ No temporary files required
- ✅ Support batch processing
- ✅ Ghostscript is already included in the project dependencies

**Disadvantages**:
- ❌ No text layer (unless the original PDF already has one)
- ❌ Compression control is rough
- ❌ Quality may not be as good as MRC

---

### Option 2: Use PyMuPDF (fitz) to compress directly

**Principle**: PyMuPDF can recompress PDF internal images

**Code Example**:
```python
import fitz

def fast_compress_pdf(input_pdf, output_pdf, quality=75):
    """Quickly compress PDF (without OCR)"""
    doc = fitz.open(input_pdf)
    
    for page in doc:
        # Get all images on the page
        image_list = page.get_images()
        
        for img in image_list:
            xref = img[0]
            #Extract image
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            
            # Recompress to JPEG
            from PIL import Image
            import io
            
            img_pil = Image.open(io.BytesIO(image_bytes))
            
            # Compress and replace
            output_buffer = io.BytesIO()
            img_pil.save(output_buffer, format='JPEG', 
                        quality=quality, optimize=True)
            output_buffer.seek(0)
            
            # Replace images in PDF
            page.replace_image(xref, stream=output_buffer.read())
    
    # Save the compressed PDF
    doc.save(output_pdf, garbage=4, deflate=True, clean=True)
    doc.close()
```

**Advantages**:
- ✅ Fast (10-30 seconds/document)
- ✅ Fine control of compression parameters
- ✅ Large images can be selectively compressed
- ✅ Keep original PDF text layer

**Disadvantages**:
- ❌ Requires processing of each image (relatively slow)
- ❌ Compression may not be as good as Ghostscript
- ❌ Does not support MRC layered compression

---

### Option 3: Use qpdf + Ghostscript combination

**Principle**: qpdf optimizes PDF structure + Ghostscript compresses images

**Command Example**:
```bash
# Step 1: qpdf optimization structure
qpdf --linearize --object-streams=generate input.pdf temp.pdf

# Step 2: Ghostscript compressed image
gs -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook \
   -dNOPAUSE -dQUIET -dBATCH \
   -sOutputFile=output.pdf temp.pdf
```

**Advantages**:
- ✅ Fast (10-20 seconds/document)
- ✅ Structure optimization + image compression
- ✅ High compression rate
- ✅ The tool is already dependent

**Disadvantages**:
- ❌ Two-step processing
- ❌ Temporary file overhead

---

## 📊 Performance comparison (estimated)

| Solution | Speed ​​(156 pages) | Compression rate | Text layer | Implementation difficulty |
|------|------------|--------|--------|---------|
| **Current (DAR+OCR)** | 4.5 hours | Extremely high | ✅ Generate | - |
| **Option 1: Ghostscript** | 10-15 seconds | High | ⚠️ Keep original | ⭐ Simple |
| **Option 2: PyMuPDF** | 30-60 seconds | Medium-High | ✅ Keep original | ⭐⭐ Medium |
| **Option 3: qpdf+gs** | 20-30 seconds | High | ⚠️ Keep the original | ⭐⭐ Medium |
| **Pro Tools** | 15 seconds | High | ❌ None | - |

---

## 🚀 Recommended implementation plan

### Phase 1: Adding Ghostscript Quick Mode

**Command line parameters**:
```bash
python main.py --input large.pdf --output out/ --fast-mode
```

**Implementation**:
1. Add `--fast-mode` parameter
2. When fast mode is detected, skip the DAR process
3. Call Ghostscript compression directly
4. Use mapping relationships:
   - S1-S2 → `/printer` (300 DPI)
   - S3-S5 → `/ebook` (150 DPI)
   - S6-S7 → `/screen` (72 DPI)

**Code modification points**:
- `main.py`: Add `--fast-mode` parameter
- `compressor/pipeline.py`: Add `fast_compress_with_ghostscript()` function
- `compressor/strategy.py`: Skip DAR in fast mode and call Ghostscript directly

---

### Phase 2: Adding smart mode selection

**Automatic detection**:
```python
def should_use_fast_mode(pdf_path):
    """Determine whether to use fast mode"""
    doc = fitz.open(pdf_path)
    
    # Check whether there is a text layer
    has_text = False
    for page in doc:
        if page.get_text().strip():
            has_text = True
            break
    
    doc.close()
    
    if has_text:
        # There is already a text layer, quick mode is recommended
        return True, "PDF already contains a text layer, it is recommended to use fast mode"
    else:
        # No text layer, full mode recommended
        return False, "PDF has no text layer, it is recommended to use full mode (including OCR)"
```

**User Interaction**:
```bash
$ python main.py --input document.pdf --output out/

Detected PDF already contains text layer
Fast mode recommended (estimated 15 seconds)

Do you want to use quick mode? [Y/n]: y

Use fast mode compression...
Done! Took 12 seconds
```

---

### Phase 3: Mixed Mode (Optimal Solution)

**Scenario**: Some pages have a text layer and some do not.

**Strategy**:
1. Analyze whether there is text on each page
2. Pages with text: quick compression
3. Page without text: complete DAR+OCR
4. Finally merge all pages

**Expected results**:
- 100 pages with text → fast compression (10 seconds)
- 56 pages without text → DAR+OCR (1 hour)
- Total time taken: 1 hour (instead of 4.5 hours)

---

## 📝 User usage scenarios

### Scenario 1: Scan (without text layer)
```bash
# Must use full mode
python main.py --input scan.pdf --output out/
# Automatically detect layers without text, use DAR+OCR
# Time taken: 4.5 hours
```

### Scenario 2: Electronic document (already has text layer)
```bash
# Recommended fast mode
python main.py --input ebook.pdf --output out/ --fast-mode
# Use Ghostscript to compress directly
# Time taken: 15 seconds
```

### Scenario 3: Mixed documents
```bash
# Automatic intelligent processing
python main.py --input mixed.pdf --output out/ --auto
# Automatic analysis, mixed use of fast + complete mode
# Time consuming: According to text page ratio
```

---

## ⚠️ Notes

### Limitations of quick mode

1. **Do not generate new text layer**
- Compress images only
- If the original PDF has no text, the output will also have no text.

2. **Compression rate may be lower**
- Ghostscript is not as sophisticated as MRC
- Expected compression ratio 50-70% (vs MRC 80-90%)

3. **Rough quality control**
- Only preset levels can be selected
- Not as finely tuned as S1-S7

### suggestion

- **Scans**: Must be in full mode (requires OCR)
- **E-book**: Prioritize quick mode (with text)
- **Not sure**: Let the program automatically detect

---

## 🎯 Summary

### Our advantages (reserved)
- ✅ Generate high-quality text layer (OCR)
- ✅ MRC compression rate is extremely high
- ✅ S1-S7 smart strategy
- ✅ Suitable for archiving and retrieval

### New capabilities (quick mode)
- ✅ Speed increased by 100-300 times
- ✅ Suitable for PDFs with existing text layers
- ✅ Simple to implement (Ghostscript)
- ✅ Maintain tool flexibility

### Final positioning
**All-in-one PDF compression tool**:
- Need OCR? → Full mode (4.5 hours)
- Just need compression? → Quick mode (15 seconds)
- Not sure? → Automatic mode (smart selection)

**Goal**: Become a professional tool that is both fast and accurate!

---

**Next step**: Implement option 1 (Ghostscript quick mode)?
