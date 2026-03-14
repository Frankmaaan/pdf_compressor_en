#!/usr/bin/env python3
"""
S7 hOCR optimized integration test script

Test whether the S7 solution correctly calls the hOCR optimization function.
"""

import sys
import tempfile
from pathlib import Path

#Add the project root directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from compressor import pipeline


def test_optimize_hocr_function():
    """Test optimize_hocr_for_extreme_compression function"""
    print("=" * 60)
    print("Test 1: hOCR optimization function unit test")
    print("=" * 60)
    
    # Create test hOCR content
    test_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" 
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
<title>Test hOCR</title>
<meta http-equiv="content-type" content="text/html; charset=utf-8" />
</head>
<body>
  <div class='ocr_page' id='page_1'>
    <div class='ocr_carea' id='carea_1_1'>
      <p class='ocr_par' id='par_1_1'>
        <span class='ocr_line' id='line_1_1'>
          <span class='ocrx_word' id='word_1_1' title='bbox 100 100 200 120'>Hello</span>
          <span class='ocrx_word' id='word_1_2' title='bbox 210 100 300 120'>World</span>
        </span>
      </p>
    </div>
  </div>
</body>
</html>"""
    
    #Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.hocr', delete=False, encoding='utf-8') as f:
        test_file = Path(f.name)
        f.write(test_content)
    
    try:
        #Record original size
        original_size = test_file.stat().st_size
        print(f"✓ Create test file: {test_file.name}")
        print(f"Original size: {original_size} bytes")
        
        #Perform optimization
        result = pipeline.optimize_hocr_for_extreme_compression(test_file)
        
        # Verify results
        optimized_size = result.stat().st_size
        print(f"  优化大小: {optimized_size} bytes")
        print(f"  减少: {original_size - optimized_size} bytes ({(1 - optimized_size / original_size) * 100:.1f}%)")
        
        # Read the optimized content
        with open(result, 'r', encoding='utf-8') as f:
            optimized_content = f.read()
        
        # Verify that the ocrx_word tag has been removed
        if 'ocrx_word' not in optimized_content:
            print("✓ ocrx_word tag has been successfully removed")
            return True
        else:
            print("✗ Error: ocrx_word tag still exists")
            return False
            
    finally:
        # cleanup
        if test_file.exists():
            test_file.unlink()
            print(f"✓ Clean test files")


def test_strategy_import():
    """Test whether strategy.py can correctly import and use the pipeline module"""
    print("\n" + "=" * 60)
    print("Test 2: Module import test")
    print("=" * 60)
    
    try:
        from compressor import strategy
        print("✓ strategy module imported successfully")
        
        # Check if the _execute_scheme function exists
        if hasattr(strategy, '_execute_scheme'):
            print("✓ _execute_scheme function exists")
        else:
            print("✗ Error: _execute_scheme function does not exist")
            return False
        
        # Check if COMPRESSION_SCHEMES contains S7
        if 7 in strategy.COMPRESSION_SCHEMES:
            s7_config = strategy.COMPRESSION_SCHEMES[7]
            print(f"✓ S7 solution configuration: {s7_config}")
            
            # Verify S7 parameters
            expected = {'name': 'S7-Ultimate', 'dpi': 72, 'bg_downsample': 10, 'jpeg2000_encoder': 'grok'}
            if s7_config == expected:
                print("✓ S7 parameter configuration is correct")
                return True
            else:
                print(f"✗ S7 parameter configuration error, expected: {expected}")
                return False
        else:
            print("✗ Error: S7 solution does not exist")
            return False
            
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_function_signature():
    """Test whether the function signature is correct"""
    print("\n" + "=" * 60)
    print("Test 3: Function signature check")
    print("=" * 60)
    
    import inspect
    
    # Check optimize_hocr_for_extreme_compression
    if hasattr(pipeline, 'optimize_hocr_for_extreme_compression'):
        func = pipeline.optimize_hocr_for_extreme_compression
        sig = inspect.signature(func)
        print(f"✓ Function signature: optimize_hocr_for_extreme_compression{sig}")
        
        # Check parameters
        params = list(sig.parameters.keys())
        if params == ['hocr_file']:
            print("✓ Parameter signature is correct")
            return True
        else:
            print(f"✗ Parameter error, expected ['hocr_file'], actual {params}")
            return False
    else:
        print("✗ function does not exist")
        return False


def main():
    """Run all tests"""
    print("\n" + "🔥" * 30)
    print("S7 hOCR optimized integration test")
    print("🔥" * 30 + "\n")
    
    results = []
    
    # Test 1: Function functionality
    results.append(("hOCR optimization function", test_optimize_hocr_function()))
    
    # Test 2: Module import
    results.append(("Module Import", test_strategy_import()))
    
    # Test 3: Function signature
    results.append(("function signature", test_function_signature()))
    
    # Aggregate results
    print("\n" + "=" * 60)
    print("Summary of test results")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ Passed" if result else "✗ Failed"
        print(f"{name:20s}: {status}")
    
    all_passed = all(r for _, r in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed! S7 integration completed.")
        print("=" * 60)
        print("\nNext step:")
        print("1. Test S7 solution using real PDF")
        print("2. Verify that the final PDF file loses the search function")
        print("3. Confirm that the volume is reduced by about 7%")
        print("4. Submit code to Git")
        return 0
    else:
        print("❌ Some tests failed, please check the code.")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
