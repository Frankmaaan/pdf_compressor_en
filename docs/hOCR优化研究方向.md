# hOCR file optimization research direction

## Important findings
**Date**: 2025-10-19
**Test File**: 156 pages PDF (136MB)
**hOCR file size**: 9.04 MB

### Key Observations
When testing 156-page PDF compression, it was found that the resulting hOCR file size reached **9.04 MB**, which is very significant for an extreme compression scenario (target 2MB).

**Impact Analysis**:
- hOCR files will be embedded in the final PDF
- hOCR of 9.04MB is equivalent to 4.5 times the target size
- hOCR may become a bottleneck in S7 Ultimate

---

## Research direction

### 1. **Empty hOCR Technology** (High Priority)

#### Concept
Preserves the structure of the hOCR file, but removes all OCR-recognized text content.

#### Expected results
According to research literature, empty hOCR can significantly reduce file size under extreme compression conditions.

#### Implementation plan
```python
def create_empty_hocr(input_hocr_file, output_hocr_file):
    """
    Create empty hOCR file (keep structure, remove text content)
    
    Reserved:
    - XML structure
    - Page information (ocr_page)
    - Area information (ocr_carea)
    - Line information (ocr_line)
    - Word bounding box (ocrx_word)
    
    Delete:
    - All text content (the bbox in the title attribute is reserved)
    """
    import xml.etree.ElementTree as ET
    
    tree = ET.parse(input_hocr_file)
    root = tree.getroot()
    
    # Traverse all elements containing text
    for elem in root.iter():
        if elem.text:
            elem.text = '' # Clear text content
        if elem.tail:
            elem.tail = '' # Clear the tail text
    
    tree.write(output_hocr_file, encoding='utf-8', xml_declaration=True)
    
    return output_hocr_file
```

#### Test plan
1. Generate raw hOCR (9.04MB)
2. Create an empty hOCR version
3. Run the S7 solution using two hOCRs respectively
4. Compare final PDF size and readability

---

### 2. **Variable DPI hOCR** ​​(medium priority)

#### Current Issues
All compression schemes (S1-S7) use hOCR files generated at 300 DPI.

#### Research questions
- S7 rebuilt with DPI=72, but hOCR was generated at 300 DPI
- Will this mismatch affect the final file size?
- Direction of influence: forward (smaller) or reverse (larger)?

#### Implementation plan
```python
def _precompute_dar_steps_variable_dpi(input_pdf_path, temp_dir, target_scheme):
    """
    Generate the corresponding hOCR according to the DPI of the target solution
    """
    scheme = COMPRESSION_SCHEMES[target_scheme]
    target_dpi = scheme['dpi']
    
    # Deconstruct using the DPI of the target scheme
    image_files = pipeline.deconstruct_pdf_to_images(
        input_pdf_path, temp_dir, dpi=target_dpi
    )
    
    # Generate hOCR corresponding to DPI
    hocr_file = pipeline.analyze_images_to_hocr(image_files, temp_dir)
    
    return {'image_files': image_files, 'hocr_file': hocr_file}
```

#### Test plan
1. S1 uses 300 DPI hOCR
2. S7 uses 72 DPI hOCR
3. Compare the effects of using different DPI hOCR with the same solution

---

### 3. **hOCR compression technology** (low priority)

#### Direction
- Use gzip to compress hOCR files
- Simplified hOCR XML structure
- Remove redundant attributes

#### Test priority
Low (verify the effects of the above two directions first)

---

## Experimental design

### Experiment 1: Empty hOCR vs original hOCR

**Test file**: testpdf156.pdf (156 pages, 136MB)

| Scheme | hOCR Type | hOCR Size | Final PDF Size | Readability |
|------|-----------|-----------|---------------|--------|
| S7 | Original (9.04MB) | 9.04MB | ? | ? |
| S7 | Empty hOCR | ? | ? | ? |

### Experiment 2: Different DPI hOCR comparison

| Scheme | DPI | hOCR DPI | hOCR Size | Final PDF Size |
|------|-----|----------|-----------|---------------|
| S7   | 72  | 300      | 9.04MB    | ?             |
| S7   | 72  | 72       | ?         | ?             |

---

## Expected revenue

### Optimistic estimate
If empty hOCR reduces file size by 50%:
- Original hOCR: 9.04MB
- Empty hOCR: ~4.5MB
- **Save**: 4.5MB

For compression tasks targeting 2MB, this is a huge improvement!

### Conservative estimate
Even if it’s only a 30% reduction:
- **Save**: 2.7MB

Still very impressive.

---

## Implementation suggestions

### Phase 1: Verify empty hOCR effect (1-2 days)
1. Implement the `create_empty_hocr()` function
2. Test on testpdf156.pdf
3. Evaluate effectiveness and readability

### Phase 2: Variable DPI Study (2-3 days)
1. Implement `_precompute_dar_steps_variable_dpi()`
2. Compare the effects of hOCR with different DPIs
3. Determine the optimal strategy

### Phase 3: Integration into production (1 day)
1. Enable empty hOCR for S7 scenario
2. Add the command line parameter `--empty-hocr`
3. Update documentation

---

## Technical details

### hOCR file structure example
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" 
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
  <title></title>
  <meta http-equiv="content-type" content="text/html; charset=utf-8" />
  <meta name='ocr-system' content='tesseract 5.3.0' />
</head>
<body>
  <div class='ocr_page' id='page_1' title='bbox 0 0 2550 3300; ppageno 0'>
    <div class='ocr_carea' id='block_1_1' title="bbox 100 200 2450 3100">
      <p class='ocr_par' id='par_1_1' title="bbox 100 200 2450 250">
        <span class='ocr_line' id='line_1_1' title="bbox 100 200 2450 250">
          <span class='ocrx_word' id='word_1_1' title='bbox 100 200 300 250'>
            Here is the recognized text <!-- This part will be deleted -->
          </span>
        </span>
      </p>
    </div>
  </div>
</body>
</html>
```

### Empty hOCR example
```xml
<!-- Keep all bbox information and delete text content -->
<span class='ocrx_word' id='word_1_1' title='bbox 100 200 300 250'></span>
```

---

## Related research

### Literature Reference
1. "Efficient PDF Compression Using Mixed Raster Content"
2. "hOCR: An Open Standard for Representing OCR Results"
3. Archive PDF Tools document’s instructions on hOCR processing

### Community Experience
- Some users reported that empty hOCR can reduce file size by 40-60%
- Suitable for scenarios where text search function is not required
- No impact on visual quality

---

## risk assessment

### Empty hOCR risk
- ❌ Loss of text search ability
- ❌ Loss of text copy function
- ✅ Preserve visual effects
- ✅ Preserve page layout

### Applicable scenarios
- Pure archiving use (no searching required)
- Extreme compression scenarios (< 2MB)
- Image PDF (OCR accuracy is low)

---

## Next action

**When continuing tomorrow**:
1. [ ] Implement the `create_empty_hocr()` function
2. [ ] Test the empty hOCR effect on testpdf156.pdf
3. [ ] Record detailed test data
4. [ ] Evaluate whether it is worth integrating into the main process

**Remarks**: The current v2.0.2 has solved all urgent issues, and hOCR optimization research can be carried out calmly.

---

**Creation date**: 2025-10-19
**Status**: Awaiting research
**Priority**: High
**Estimated workload**: 4-6 days
