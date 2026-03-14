# PDF compression and splitting tool

An automatic compression and splitting tool for professional title declaration PDF files based on archive-pdf-tools, which implements the "Deconstruction-Analysis-Reconstruction" (DAR) three-stage processing process.

## Features

- **Biary Bidirectional Search Compression**: Use intelligent algorithms to quickly find the best quality parameters
- **6 scheme strategy optimization**: S1-S6 six-level compression scheme, automatically selecting the best quality
- **Pure physical split**: No re-compression during splitting, reuse the intermediate results of compression
- **Batch Processing**: Supports batch processing of single files and directories
- **Detailed Log**: Complete processing records and error tracking
- **English Support**: Optimized English OCR recognition
- **Manual Mode**: Supports interactive manual input of compression parameters

## Technical architecture

### DAR three-stage process

1. **Deconstruct**: Use `pdftoppm` to convert PDF to high-quality images
2. **Analyze**: Use `tesseract` to perform OCR and generate hOCR files
3. **Reconstruct**: Use `recode_pdf` to reconstruct and optimize PDF based on MRC technology

### Layered compression strategy

The project uses **Biary Bidirectional Search Algorithm** and defines 7 compression schemes (S1-S7):

- **S1** (dpi=300, bg_downsample=2): high quality starting point, conservative compression
- **S2** (dpi=300, bg_downsample=3): moderate downsampling, gentle compression
- **S3** (dpi=250, bg_downsample=3): Balance mass and volume
- **S4** (dpi=200, bg_downsample=4): aggressive compression
- **S5** (dpi=150, bg_downsample=5): Aggressive compression
- **S6** (dpi=100, bg_downsample=8): Extreme compression
- **S7** (dpi=72, bg_downsample=10): Ultimate compression ⚠️ **You will lose the text search function, but you can reduce the size by about 7%**

**Search Strategy**:
1. Try it from S1
2. If S1 fails and the result is >1.5 times the target, jump directly to S7 (ultimate solution)
3. If S7 is successful, backtrack upward (S6→S5→...) to find the best quality
4. Otherwise, search progressively in the order S1→S2→S3...

**Special Note for S7**: The S7 solution will automatically optimize hOCR files (removing text tags), which can reduce the size by an additional 7%, but the generated PDF will lose text search and copy functions. This is a trade-off designed for extreme compression scenarios.

## Installation requirements

### System environment

**Only supports Ubuntu/WSL environment:**
- Ubuntu 24.04+ or WSL2 (recommended)
- Python 3.7+
- At least 2GB of free disk space (for temporary files)

**Note**: This project is designed and tested for Ubuntu/WSL environment and does not support other operating systems.

### Important note: pipx installation method

This tool uses `pipx` to install `archive-pdf-tools` to avoid contaminating the system Python environment. The installation script automatically handles Ubuntu version compatibility issues.

If you have installed archive-pdf-tools using pip before, it is recommended to uninstall it first:
```bash
pip3 uninstall archive-pdf-tools
```

### System tool dependencies

Install necessary tools in Ubuntu/WSL environment:

```bash
# Update package manager
sudo apt update

#Install core tools
sudo apt install poppler-utils tesseract-ocr tesseract-ocr-eng qpdf pipx

#Install archive-pdf-tools (pipx is recommended)
pipx install archive-pdf-tools

# Make sure PATH is configured correctly
pipx ensurepath
source ~/.bashrc
```

### Python environment

- Python 3.7+
- Standard library modules (no additional installation required)

## How to use

### Quick Start for Windows users

```batch
# Use Windows batch script (automatically handles WSL configuration)
pdf_compress.bat C:\Documents\test.pdf

# Allow split batch processing
pdf_compress.bat C:\Documents\PDFs --allow-splitting --target-size 8.0
```

### Linux/WSL users

#### Basic usage

```bash
# Process a single file (split allowed)
python main.py --input document.pdf --output ./output --allow-splitting

# Process the entire directory
python main.py --input ./pdf_folder --output ./processed

# Custom target size
python main.py --input large.pdf --output ./output --target-size 8.0
```

### Command line parameters

| Parameters | Type | Default value | Description |
|------|------|--------|------|
| `--input` | Required | - | Input PDF file or directory path |
| `--output` | Required | - | Output directory path |
| `--target-size` | Optional | 2.0 | Target file size (MB) |
| `--allow-splitting` | Optional | False | Allow splitting of files |
| `--max-splits` | Optional | 4 | Maximum number of splits (2-10) |
| `--copy-small-files` | Optional | False | Copy small files to the output directory |
| `--check-deps` | Optional | False | Only check dependencies |
| `--verbose` | Optional | False | Show detailed debugging information |
| `-k, --keep-temp-on-failure` | Optional | False | Keep temporary directory on failure |
| `-?, --examples` | Optional | False | Show usage examples |
| `-m, --manual` | Optional | False | Enter manual mode |

### Usage examples

```bash
# Check tool dependencies
python main.py --check-deps

# Process a single file (compress single.pdf to target 5MB and output to out/)
python main.py --input single.pdf --output out --target-size 5

# Run on bulk directories, allowing splitting and retaining temporary directories for debugging failures
python main.py --input ./pdfs --output ./out --target-size 3 --allow-splitting --max-splits 4 -k

# Only check dependencies, do not perform compression (for diagnostics)
python main.py --check-deps

#Quickly output common command examples
python main.py -?

# Enter interactive manual mode
python main.py --manual
```

## Project structure

```
pdf_compressor/
├── main.py # Main program entry
├── orchestrator.py # Business process scheduler
├── compressor/
│   ├── __init__.py
│ ├── pipeline.py # DAR three-stage process implementation
│ ├── strategy.py # Layered compression strategy
│ ├── splitter.py # PDF splitting logic
│ └── utils.py # Utility function
├── logs/
│ └── process.log # Processing log (automatically generated)
├── docs/ # Project documentation
├── requirements.txt # Python dependencies
└── README.md # Project description
```

## Algorithm description

### Binary bidirectional search algorithm

The program uses intelligent search algorithms to quickly find the best quality parameters:

1. **Progressive Search**: Start from S1 and return directly if successful
2. **Quick Jump**: If S1 fails and the result far exceeds the target (>1.5 times), jump directly to S6
3. **Backtracking**: If S6 is successful, test S5, S4... to find the best quality
4. **Sequential attempts**: If the jump conditions are not met, try in sequence S1→S2→S3...

**Advantages**:
- Reduce unnecessary intermediate attempts
- Maximize quality while meeting size requirements
- DAR stages 1-2 are only executed once, and all schemes reuse intermediate results.

### Split strategy

Start the **Purely Physical Splitting** protocol when compression fails:

1. **Smart Source Selection**: Select the largest file ≤8MB from all intermediate results as the split source
2. **Density Calculation**: Estimate the optimal number of splits based on file size
3. **Physical split**: Split directly using qpdf without recompression
4. **Page Allocation**: Evenly allocate pages to each shard based on density.

**Advantages**:
- Avoid repeated compression and directly use the best intermediate results
- Based on density allocation, more reasonable than simple average paging
- Significantly improve the efficiency of processing large files

## Logging and Monitoring

### Log file

- **Location**: `logs/process.log`
- **Content**: Detailed processing process, parameter selection, error message
- **Format**: timestamp + log level + module information + message

### Process report

`processing_report.txt` is automatically generated after batch processing, including:
- Process statistics
- List of successful/failed files
- Processing time recording

## Performance considerations

### Processing time

- **Single page document**: usually 30 seconds-2 minutes
- **Multi-page documents**: linear growth by the number of pages
- **Large Files**: May take 10-30 minutes

### Influencing factors

- PDF page count and complexity
- Image resolution settings
- System hardware performance
- OCR processing complexity

### Optimization suggestions

-Allow sufficient time for high-volume tasks
- Run on a machine with better performance
- Consider using an SSD to store temporary files

## troubleshooting

### FAQ

1. **Tool not found error**
   ```bash
   # Check tool installation
   python main.py --check-deps
   
   # Reinstall missing tools
   sudo apt install poppler-utils tesseract-ocr qpdf pipx
   pipx install archive-pdf-tools
   ```

2. **recode_pdf command not found**
   ```bash
   # Make sure the pipx path is in PATH
   pipx ensurepath
   source ~/.bashrc
   ```

3. **Insufficient memory**
- Reduce the number of concurrently processed files
- Lower initial DPI settings
- Make sure there is enough disk space to store temporary files

4. **OCR recognition error**
- Check tesseract language pack installation
- Try increasing the image resolution
- Confirm PDF content clarity

5. **Permission issues**
   ```bash
   # Make sure the output directory has write permissions
   chmod 755 output_directory
   ```

### Detailed Exclusion Guide

View the complete troubleshooting guide: `docs/TROUBLESHOOTING.md`

### Debugging Tips

- Use the `--verbose` parameter to view detailed information
- Check the `logs/process.log` file
- Process problem files one by one to locate the problem

## Technical support

### Log analysis

Important log information:
- `Phase 1 [Deconstruction]`: PDF to image process
- `Phase 2 [Analysis]`: OCR processing
- `Phase 3 [Reconstruction]`: PDF reconstruction process
- `Compression result size`: the result of each attempt

### contact information

In case of technical issues, please provide:
1. Complete error message
2. `logs/process.log` file
3. Basic information of the problem file (size, number of pages, etc.)
4. Commands and parameters used

## License

This project is open source under the MIT license.

## Update log

### v2.0.3 (2025-10-19)
- **Performance Optimization**: Use LZW compression when generating TIFF files, reducing temporary file size by 68% (25MB→8MB/page)
- **New**: S7 ultimate compression solution (DPI=72, BG-Downsample=10, automatic hOCR optimization)
- **Optimization**: The S7 solution automatically removes hOCR text tags, which can reduce the final PDF size by an additional 7%.
- **Trade-off**: The PDF generated by the S7 solution will lose the text search function (applicable to extreme compression scenarios)
- **Documentation**: Update compression strategy description, add S7 special instructions

### v2.0.2 (2025-10-18)
- **Bug fix**: Fix S7 solution parameter configuration problem
- **Optimization**: Improve log output format

### v2.0.0 (2025-10-18)
- **Breaking Update**: Completely rewritten compression and splitting algorithms
- Newly added: binary bidirectional search algorithm (6 plan strategy)
- New: Pure physical splitting strategy (reuse intermediate results)
- New: Manual mode supports interactive parameter input
- Added: Parameter example display (-? parameter)
- Optimization: UTF-8 encoding support, solving Windows English display problems
- Optimization: Parameter name simplification (--output-dir → --output)
- Improvement: unit testing covers all algorithm branches

### v1.0.0 (2024-10-09)
- Initial version release
- Implement a complete DAR processing process
- Support layered compression strategy
- Integrated PDF splitting function
- Add detailed logging
