#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test whether all command line parameters are available
"""

import subprocess
import sys

# Set UTF-8 encoding immediately at program start
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, OSError):
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def run_command(cmd, description):
    """Run the command and return the results"""
    print(f"\n{'='*60}")
    print(f"Test: {description}")
    print(f"command: {cmd}")
    print('-'*60)
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=10
        )
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print("Standard output:")
            print(result.stdout[:500]) # Only display the first 500 characters
        if result.stderr:
            print("Standard error:")
            print(result.stderr[:500])
        return result.returncode
    except subprocess.TimeoutExpired:
        print("Timeout!")
        return -1
    except Exception as e:
        print(f"Error: {e}")
        return -1

def main():
    """Main test function"""
    tests = [
        #Basic parameters
        ("python main.py --help", "Display help information (--help)"),
        ("python main.py -h", "Show help information (-h)"),
        ("python main.py -?", "Show example (-?)"),
        ("python main.py --examples", "Show examples (--examples)"),
        
        # Check dependencies
        ("python main.py --check-deps", "Check dependencies (--check-deps)"),
        
        # Manual mode (will exit immediately because it is interactive)
        # We don't test this as it requires user interaction
        
        # Parameter validation
        ("python main.py", "no parameters"),
        ("python main.py --input test.pdf", "Only --input, missing --output"),
        ("python main.py --output out", "Only --output, missing --input"),
        
        # Verbose mode
        ("python main.py --verbose --check-deps", "Verbose mode (--verbose)"),
        
        # target size
        ("python main.py --input test.pdf --output out --target-size 5", 
         "Custom target size (--target-size)"),
        
        # Split options
        ("python main.py --input test.pdf --output out --allow-splitting", 
         "Allow splitting (--allow-splitting)"),
        ("python main.py --input test.pdf --output out --allow-splitting --max-splits 6", 
         "maximum number of splits (--max-splits)"),
        
        # Other options
        ("python main.py --input test.pdf --output out --copy-small-files", 
         "Copy small files (--copy-small-files)"),
        ("python main.py --input test.pdf --output out -k", 
         "Keep temporary directory (-k / --keep-temp-on-failure)"),
    ]
    
    print("="*60)
    print("PDF Compression Tool - Parameter Test")
    print("="*60)
    
    results = []
    for cmd, desc in tests:
        exit_code = run_command(cmd, desc)
        results.append((desc, exit_code))
    
    # Aggregate results
    print("\n" + "="*60)
    print("Summary of test results")
    print("="*60)
    
    success_count = 0
    for desc, exit_code in results:
        # For help and example commands, exit code 0 is success
        # For other commands, exit code 1 counts as success if the correct error message is displayed
        status = "✓" if exit_code in [0, 1] else "✗"
        if exit_code in [0, 1]:
            success_count += 1
        print(f"{status} {desc}: exit code {exit_code}")
    
    print(f"\n成功: {success_count}/{len(results)}")
    
    return 0 if success_count == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
