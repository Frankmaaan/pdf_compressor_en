# hOCR Optimization Study - Quick Start Guide

## 🎯 Research Objectives

In the 156-page PDF test, the hOCR file was found to reach **9.04 MB**, which is a huge bottleneck for extreme compression.
This study aims to find the optimal hOCR optimization strategy to maximize file size reduction without affecting PDF generation.

---

## 📋 Completed work

### 1. ✅ Theoretical analysis
- 📄 `docs/hOCR Structure Depth Analysis.md` - Detailed structure analysis document
- 📄 `docs/hOCR Optimization Research Direction.md` - Research direction planning

### 2. ✅ Tool development
- 🛠️ `test_hocr/hocr_analyzer.py` - hOCR analysis and optimization tool
- 📝 `test_hocr/sample_hocr.html` - hOCR sample file

### 3. ✅ Experimental framework
The tool can automatically generate 4 optimized versions:
- **Empty text version**: Delete the text content in the `ocrx_word` tag
- **Minimized version**: Simplify attributes, only keep bbox
- **Wordless version**: Completely remove the `ocrx_word` tag
- **Textless line version**: Remove `ocr_line` tag

---

## 🚀 Next steps

### Step 1: Generate real hOCR files

Run the compression task, keeping a temporary directory to get hOCR files:

```bash
# In WSL/Ubuntu environment
cd ~/pdf_compressor
python main.py -i testpdf156.pdf -o output -t 2 --keep-temp-on-failure
```

The temporary directory location is usually `/tmp/tmpXXXXXX/combined.hocr`

### Step 2: Analyze hOCR file

```bash
# Copy hOCR to the project directory
cp /tmp/tmpXXXXXX/combined.hocr test_hocr/real_hocr.html

# Run analysis tools
python test_hocr/hocr_analyzer.py test_hocr/real_hocr.html
```

**Output**:
- Detailed structural analysis report
- 4 optimized version files
- Size comparison table

### Step 3: Test PDF generation

Use each optimized version to test whether the PDF can be generated properly:

```bash
# Enter the temporary directory
cd /tmp/tmpXXXXXX

# Back up original hOCR
cp combined.hocr combined_original.hocr

# Test 1: Empty text version
cp ~/pdf_compressor/test_hocr/hocr_experiments/combined_empty.hocr combined.hocr
recode_pdf --from-imagestack page-*.tif \
           --hocr-file combined.hocr \
           --dpi 72 --bg-downsample 10 \
           --mask-compression jbig2 -J grok \
           -o test_empty.pdf

# Check file size
ls -lh test_empty.pdf

# Test 2: Minimized version
cp ~/pdf_compressor/test_hocr/hocr_experiments/combined_minimal.hocr combined.hocr
recode_pdf --from-imagestack page-*.tif \
           --hocr-file combined.hocr \
           --dpi 72 --bg-downsample 10 \
           --mask-compression jbig2 -J grok \
           -o test_minimal.pdf

ls -lh test_minimal.pdf

# Test 3: No word version
cp ~/pdf_compressor/test_hocr/hocr_experiments/combined_no_words.hocr combined.hocr
recode_pdf --from-imagestack page-*.tif \
           --hocr-file combined.hocr \
           --dpi 72 --bg-downsample 10 \
           --mask-compression jbig2 -J grok \
           -o test_no_words.pdf

ls -lh test_no_words.pdf

# Compare to original version
cp combined_original.hocr combined.hocr
recode_pdf --from-imagestack page-*.tif \
           --hocr-file combined.hocr \
           --dpi 72 --bg-downsample 10 \
           --mask-compression jbig2 -J grok \
           -o test_original.pdf

ls -lh test_original.pdf

# Compare all versions
ls -lh test_*.pdf
```

### Step 4: Record the results

Create a test results table:

| hOCR version | hOCR size | PDF generation | PDF size | reduction | visual quality |
|-----------|-----------|--------------|----------|--------|----------|
| Original (9.04MB) | 9.04 MB | ✓ | ? MB | - | ✓ |
| empty text | ? MB | ? | ? MB | ? MB | ? |
| Minimize | ? MB | ? | ? MB | ? MB | ? |
| No words | ? MB | ? | ? MB | ? MB | ? |
| No lines of text | ? MB | ? | ? MB | ? MB | ? |

---

## 📊 Expected results

### Conservative estimate (based on sample analysis)

The sample file shows:
- Empty text version: **-3.3%**
- Minimized version: **-10.4%**
- No word version: **-44.0%**
- Line version without text: **-27.7%**

For real hOCR of 9.04MB:
- Empty text version: May reduce **0.3-4.5 MB**
- Minimized version: may reduce **0.9-5.9 MB**
- Wordless version: May reduce **4.0-6.8 MB** ⭐

**Key**: The real file may have a higher proportion of text (more English content), and the actual reduction may exceed estimates.

---

## ⚠️ Notes

### 1. Loss of functionality
All optimized versions will **lose PDF searchability**:
- ❌ Unable to search text
- ❌ Unable to copy text
- ✅ Visual effects remain unchanged
- ✅ File size significantly reduced

### 2. Compatibility risk
- **Empty text version**: low risk, retains all structure
- **Minimized version**: Risky, simplified attributes
- **Wordless version**: High risk, remove word-level positioning
- **Textless Line Version**: High risk, remove line level positioning

### 3. Recommended strategy
Priority test order:
1. **Empty text version** ⭐⭐⭐ The safest and expected to be effective
2. **Minimized version** ⭐⭐ Additional optimization, need to verify
3. **Wordless version** ⭐ Radical optimization, may fail

---

## 🔧 Integrate into production code

If the test is successful, add in `pipeline.py`:

```python
def optimize_hocr_for_compression(hocr_file: Path, strategy: str = 'empty') -> Path:
    """
    Optimizing hOCR files for extreme compression
    
    Args:
        hocr_file: original hOCR file path
        strategy: optimization strategy
        - 'empty': delete text content (recommended)
        - 'minimal': simplified attributes
        - 'none': no optimization
    
    Returns:
        Optimized hOCR file path
    """
    if strategy == 'none':
        return hocr_file
    
    with open(hocr_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if strategy == 'empty':
        # Delete the text content in the ocrx_word tag
        optimized_content = re.sub(
            r'(<span[^>]*?ocrx_word[^>]*?>)([^<]+)(</span>)',
            r'\1\3',
            content
        )
    elif strategy == 'minimal':
        # Delete the text first
        optimized_content = re.sub(
            r'(<span[^>]*?ocrx_word[^>]*?>)([^<]+)(</span>)',
            r'\1\3',
            content
        )
        # Simplify the attributes again
        def simplify_title(match):
            full_title = match.group(1)
            bbox_match = re.search(r'bbox \d+ \d+ \d+ \d+', full_title)
            if bbox_match:
                return f'title="{bbox_match.group()}"'
            return match.group(0)
        
        optimized_content = re.sub(
            r'title="([^"]*)"',
            simplify_title,
            optimized_content
        )
    else:
        raise ValueError(f"Unknown strategy: {strategy}")
    
    # Save the optimized file
    optimized_file = hocr_file.parent / f"{hocr_file.stem}_optimized.hocr"
    with open(optimized_file, 'w', encoding='utf-8') as f:
        f.write(optimized_content)
    
    return optimized_file
```

Enable for S7 scenario in `strategy.py`:

```python
def _precompute_dar_steps(input_pdf_path, temp_dir):
    """Perform a one-time deconstruction and analysis step"""
    # ... existing code ...
    
    # Optimize hOCR for extreme compression
    if getattr(args, 'optimize_hocr', False):
        hocr_file = optimize_hocr_for_compression(hocr_file, strategy='empty')
    
    return {'image_files': image_files, 'hocr_file': hocr_file}
```

Add command line parameters:

```python
parser.add_argument('--optimize-hocr', 
                    action='store_true',
                    help='Optimize hOCR files to reduce final PDF size (loss of search functionality)')
```

---

## 📈 Success Criteria

Conditions for successful experiment:
1. ✅ PDF can be generated successfully
2. ✅ No significant degradation in visual quality
3. ✅ File size is significantly reduced (> 2MB)
4. ✅ There is no significant increase in the execution time of recode_pdf

If the above conditions are met, the optimization strategy is worth integrating into the production environment.

---

## 📝 Next step experiment checklist

- [ ] Run compression task to generate real hOCR files
- [ ] Use hocr_analyzer.py to analyze files
- [ ] Test whether the empty text version can generate PDF
- [ ] Test whether the minimized version can generate PDF
- [ ] Test whether the wordless version can generate PDF
- [ ] Compare PDF sizes of all versions
- [ ] Check visual quality
- [ ] Record detailed test results
- [ ] Select the optimal strategy
- [ ] integrated into code
- [ ] Update documentation

---

## 💡 Expected impact

If empty text optimization is successful, for a 156 page PDF:
- hOCR: 9.04MB → about 6MB (reduced by 3MB)
- Final PDF: Possibly from impossible to 2MB → able to 2MB
- **This will be a breakthrough improvement! ** 🎉

---

**Creation date**: 2025-10-19
**Status**: Ready for testing
**Next step**: Get real hOCR files for experimentation
