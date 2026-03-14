# hOCR file structure in-depth analysis

## 📚 hOCR Introduction

**hOCR** ​​(HTML-based OCR) is an open standard for representing OCR results in HTML/XHTML.

### Core Purpose
1. **Text coordinate positioning**: Record the precise position of each word/character on the page
2. **Text content storage**: Save the text content recognized by OCR
3. **PDF Searchability**: Embed PDF to enable text search and copy functions
4. **Layout information**: Preserve the hierarchical structure of pages, paragraphs, and lines

---

## 🏗️ hOCR file structure hierarchy

```
HTML document
└── <body>
    └── <div class="ocr_page"> # Page level
    └── <div class="ocr_carea"> # Content area
    └── <p class="ocr_par"> # Paragraph
    └── <span class="ocr_line"> # Text line
    └── <span class="ocrx_word"> # word/phrase
    text content
```

---

## 📋 Tag detailed analysis

### 1. `ocr_page` - page container

**Function**: Represents a complete page

**Key Attributes**:
```html
<div class='ocr_page' id='page_1' title='bbox 0 0 2550 3300; ppageno 0'>
```

- `bbox 0 0 2550 3300`: page bounding box (upper left corner x,y to lower right corner x,y)
- `ppageno 0`: physical page number (starting from 0)

**Impact on file size**:
- A small amount (one per page)
- Contains page size information, which must be retained

**Can be deleted**: ❌ No - must be retained for page positioning

---

### 2. `ocr_carea` - content area

**Function**: Represents a content area in the page (such as text block, picture area)

**Key Attributes**:
```html
<div class='ocr_carea' id='block_1_1' title="bbox 100 200 2450 3100">
```

- `bbox`: area bounding box
- `id`: unique identifier

**Impact on file size**:
- Medium (may have multiple areas per page)
- Provide coarse-grained layout information

**Can it be deleted**: ⚠️ Possible - need to test whether recode_pdf is dependent on it

---

### 3. `ocr_par` - Paragraph

**Function**: Represents a paragraph

**Key Attributes**:
```html
<p class='ocr_par' id='par_1_1' lang='zho' title="bbox 100 200 2450 500">
```

- `lang`: language code (zho=English, eng=English)
- `bbox`: Paragraph bounding box

**Impact on file size**:
- Medium (may have multiple paragraphs per content area)
- Provide paragraph level layout

**Can it be deleted**: ⚠️ Possible - needs to be tested

---

### 4. `ocr_line` - Text line ⭐ Important

**Function**: Represents a line of text

**Key Attributes**:
```html
<span class='ocr_line' id='line_1_1' 
      title="bbox 100 200 2450 250; baseline -0.002 -5; x_size 45; x_descenders 10; x_ascenders 10">
```

- `bbox`: row bounding box
- `baseline`: baseline offset
- `x_size`: font size
- `x_descenders`: Descenders
- `x_ascenders`: ascending parts

**Impact on file size**:
- 🔴 **High** - Large quantity, detailed attributes
- Contains extensive font metric information

**Can it be deleted**: ⚠️ Possible - or simplify attributes (only keep bbox)

---

### 5. `ocrx_word` - word/phrase ⭐⭐⭐ the most critical

**Function**: Represents a word or phrase, containing actual text content

**Key Attributes**:
```html
<span class='ocrx_word' id='word_1_1' title='bbox 100 200 300 250; x_wconf 95'>
    this is the first
</span>
```

- `bbox`: word bounding box
- `x_wconf`: recognition confidence (0-100)
- **In-label text**: The actual text recognized by OCR

**Impact on file size**:
- 🔴🔴🔴 **Extremely High** - Highest number, including all texts
- Text content takes up a lot of space
- English characters especially take up space (UTF-8 3 bytes per character)

**Can it be deleted**:
- The tag itself: ⚠️ may need to be retained (recode_pdf may need positioning information)
- Text content: ✅ **Can be deleted! **(This is the key to optimization)

---

## 🎯 Optimization strategy analysis

### Strategy 1: Remove text content (empty hOCR) ⭐⭐⭐

**Action**: Keep all tags and bboxes, delete only the text within the `ocrx_word` tag

```html
<!-- Original -->
<span class='ocrx_word' id='word_1_1' title='bbox 100 200 300 250'>This is text</span>

<!-- After optimization -->
<span class='ocrx_word' id='word_1_1' title='bbox 100 200 300 250'></span>
```

**Expected results**:
- Text accounts for about 30-50% (higher for English)
- **Estimated reduction**: 30-50% file size
- **RISK**: Loss of search functionality (but we don’t need it)

**Difficulty of implementation**: ⭐ Simple (regular replacement)

---

### Strategy 2: Simplified attributes (minimal hOCR) ⭐⭐

**Operation**: Delete non-essential attributes and keep only bbox

```html
<!-- Original -->
<span class='ocr_line' id='line_1_1' 
      title="bbox 100 200 2450 250; baseline -0.002 -5; x_size 45; x_descenders 10; x_ascenders 10">

<!-- After optimization -->
<span class='ocr_line' id='line_1_1' title="bbox 100 200 2450 250">
```

**Expected results**:
- **Estimated reduction**: 10-15% additional space
- **RISK**: recode_pdf may require certain attributes

**Difficulty of implementation**: ⭐⭐ Medium (needs to test compatibility)

---

### Strategy 3: Remove the entire ocrx_word tag ⭐

**Action**: Completely remove the `<span class="ocrx_word">` tag

```html
<!-- Original -->
<span class='ocr_line' id='line_1_1' title="...">
  <span class='ocrx_word' id='word_1_1' title='...'>文本1</span>
  <span class='ocrx_word' id='word_1_2' title='...'>文本2</span>
</span>

<!-- After optimization -->
<span class='ocr_line' id='line_1_1' title="...">
</span>
```

**Expected results**:
- **Estimated reduction**: 50-70% file size
- **Risk**: ⚠️ High - recode_pdf may rely on word-level targeting

**Difficulty of Implementation**: ⭐ Simple

---

### Strategy 4: Remove ocr_line tag ⭐

**Action**: Remove text line level structure

**Expected results**:
- **Estimated reduction**: 60-80% file size
- **Risk**: 🔴 Very high - may cause recode_pdf to fail

**Difficulty of Implementation**: ⭐ Simple

---

## 🔬 Experimental Plan

### Stage 1: File size analysis (no need to rebuild PDF)

1. ✅ **Analyze raw hOCR**
- Measure total size
- Count the number of elements at each level
- Calculate the proportion of text content

2. ✅ **Create optimized version**
- Empty text version (remove ocrx_word text)
- Minimal version (simplified attributes)
- Wordless version (remove ocrx_word tag)
- No text line version (remove ocr_line tag)

3. ✅ **Compare size**
- Record the file size of each version
- Calculate reduction percentage

### Phase 2: PDF Reconstruction Test

Test each optimized version with a real PDF:

```bash
# Test command
recode_pdf --from-imagestack /tmp/page-*.tif \
           --hocr-file <optimized hocr file> \
           --dpi 72 \
           --bg-downsample 10 \
           --mask-compression jbig2 \
           -J grok \
           -o test_output.pdf
```

**Test Matrix**:
| hOCR version | Can PDF be generated | PDF size | Readability | Searchability |
|-----------|--------------|----------|--------|----------|
| Original | ✓ | ? | ✓ | ✓ |
| empty text | ? | ? | ? | ✗ |
| Minimize | ? | ? | ? | ✗ |
| No words | ? | ? | ? | ✗ |
| No text lines | ? | ? | ? | ✗ |

### Phase 3: Integration into production

Based on the test results, select the optimal strategy:

```python
def optimize_hocr_for_compression(hocr_file, strategy='empty_text'):
    """
    Optimizing hOCR files for extreme compression
    
    Args:
        hocr_file: original hOCR file path
        strategy: optimization strategy
        - 'empty_text': delete text content (recommended)
        - 'minimal': simplified attributes
        - 'no_words': delete word tags
    
    Returns:
        Optimized hOCR file path
    """
    pass
```

---

## 📊 Expected revenue (based on 9.04MB hOCR)

### Conservative estimate

| Strategy | Reduce Rate | Saving Space | Notes |
|------|--------|----------|------|
| Empty text | 30% | 2.7 MB | Most secure |
| Minimize | 40% | 3.6 MB | Medium Risk |
| No words | 60% | 5.4 MB | High risk |

### Optimistic estimate

| Strategy | Reduce Rate | Saving Space | Notes |
|------|--------|----------|------|
| Empty text | 50% | 4.5 MB | High proportion of text |
| Minimized | 65% | 5.9 MB | Successfully simplified attributes |
| No words | 75% | 6.8 MB | recode_pdf does not depend on |

**Key takeaway**: Even with a conservative estimate, the empty text strategy saves **2.7 MB**, which is extremely critical against the 2MB target!

---

## 🛠️ Implementation tools

The `hocr_analyzer.py` tool has been created, containing:

1. ✅ `HocrAnalyzer` class
2. ✅ `analyze_structure()` - Structural analysis
3. ✅ `create_empty_hocr()` - Create an empty text version
4. ✅ `create_minimal_hocr()` - Create a minimal version
5. ✅ `create_no_words_hocr()` - Create a word-free version
6. ✅ `create_no_lines_hocr()` - Create lines without text
7. ✅ `run_hocr_experiments()` - complete experiment process

---

## 📝 Usage example

```bash
# Analyze real hOCR files
python test_hocr/hocr_analyzer.py /tmp/tmpxxx/combined.hocr

# Output:
# - Structural Analysis Report
# - Files for each optimized version
# - Size comparison table
```

---

## 🔍 Summary of key findings

1. **Text content is the largest percentage** - maybe 30-50%
2. **ocrx_word tags at most** - one for each word
3. **English takes up more space** - UTF-8 encoding, 3 bytes per character
4. **bbox information must be retained** - recode_pdf requires coordinate positioning
5. **Safest to delete text content** - keep all structure and coordinates

---

## Next action

1. [ ] Run `hocr_analyzer.py` to analyze the real 9.04MB hOCR file
2. [ ] Test whether each optimized version can successfully generate PDF
3. [ ] Compare final PDF size
4. [ ] Select the optimal strategy
5. [ ] integrated into `pipeline.py`

---

**Creation date**: 2025-10-19
**Research Status**: Ready
**Expected Benefit**: 2.7-6.8 MB file size reduction
