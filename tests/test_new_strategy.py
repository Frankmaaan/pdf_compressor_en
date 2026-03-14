# tests/test_new_strategy.py

import unittest
import sys
import shutil
from pathlib import Path
import logging

# Add the project root directory to sys.path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from compressor import strategy, utils
from compressor import pipeline

# --- Simulation (Monkey-Patch) core function ---

# Mapping relationship between simulated compression scheme and file size
# (dpi, bg_downsample) -> size_mb
FAKE_SIZE_MAP = {
    (300, 2): 30.0,  # S1
    (300, 3): 15.0,  # S2
    (250, 3): 8.0,   # S3
    (200, 4): 4.0,   # S4
    (150, 5): 1.8,   # S5
    (110, 6): 0.9,   # S6
}

def fake_deconstruct(pdf_path, temp_dir, dpi):
    """Simulate the deconstruction process and return a fake image path list."""
    logging.debug(f"SIMULATE: Deconstructing {pdf_path} in {temp_dir} with dpi {dpi}")
    # Create temporary directory if it does not exist
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    return [Path(temp_dir) / f"page-{i:02d}.tif" for i in range(1, 11)]

def fake_analyze(images, temp_dir):
    """Simulate the analysis process and return the fake hocr file path."""
    logging.debug(f"SIMULATE: Analyzing images in {temp_dir}")
    hocr_path = Path(temp_dir) / "combined.hocr"
    hocr_path.touch() # Create an empty hocr file
    return hocr_path

def fake_reconstruct(images, hocr, temp_dir, params, output_pdf_path):
    """
    Simulate the reconstruction process.
    Find the corresponding file size from FAKE_SIZE_MAP based on the passed 'dpi' and 'bg_downsample' parameters,
    And create a fake PDF file with content of that size (in the form of a string).
    """
    dpi = params.get('dpi', 300)
    bg = params.get('bg_downsample', 1)
    
    # Find the corresponding simulation size
    size_mb = FAKE_SIZE_MAP.get((dpi, bg))
    if size_mb is None:
        # If the scheme is not defined in MAP, return a default large file size
        size_mb = 50.0
        
    logging.debug(f"SIMULATE: Reconstructing to {output_pdf_path} with params {params}, fake size: {size_mb}MB")
    
    # Create a fake PDF file, the file content is its size
    with open(output_pdf_path, 'w') as f:
        f.write(str(size_mb))
        
    return True

def fake_get_file_size_mb(file_path):
    """Simulate obtaining the file size and directly read the content of the fake PDF file (that is, its size)."""
    try:
        with open(file_path, 'r') as f:
            size = float(f.read())
            logging.debug(f"SIMULATE: Getting size for {file_path}: {size}MB")
            return size
    except (IOError, ValueError):
        # For the original input file, return a preset larger value
        logging.debug(f"SIMULATE: Getting size for original file {file_path}: 40MB")
        return 40.0

#Apply simulation patch
pipeline.deconstruct_pdf_to_images = fake_deconstruct
pipeline.analyze_images_to_hocr = fake_analyze
pipeline.reconstruct_pdf = fake_reconstruct
utils.get_file_size_mb = fake_get_file_size_mb

class TestNewCompressionStrategy(unittest.TestCase):

    def setUp(self):
        """Run before each test to set up the test environment."""
        self.test_dir = Path('./test_temp_output')
        self.test_dir.mkdir(exist_ok=True)
        self.input_pdf = self.test_dir / 'dummy_input.pdf'
        self.input_pdf.touch() # Create an empty input file
        # Configure the logger to view the output of the simulation process
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    def tearDown(self):
        """Run after each test to clean up the test environment."""
        shutil.rmtree(self.test_dir)

    def test_compression_success_progressive(self):
        """
        Test success scenario (progressive):
        - Target size: 10MB
        - S1 (30MB) > 1.5 * 10MB (15MB) -> not satisfied, so it is > 1.5x
        - Expected: Jump to S6 (0.9MB), successful. Then backtrack to S5(1.8), S4(4), S3(8). S2(15) is too large.
        - The best option would be S3.
        """
        logging.info("\n--- Running test_compression_success_jump_and_backtrack ---")
        target_size = 10.0
        status, details = strategy.run_compression_strategy(self.input_pdf, self.test_dir, target_size)
        
        self.assertEqual(status, 'SUCCESS')
        self.assertEqual(details['best_scheme_id'], 3) # S3 is the best solution
        self.assertIn('final_path', details)
        self.assertTrue(Path(details['final_path']).exists())

    def test_compression_success_jump_and_backtrack(self):
        """
        Test success scenario (jump backtracking):
        - target_size = 20MB
        - S1 (30MB) <= 1.5 * 20MB (30MB) -> satisfied
        - Expectation: Take the gradual route S1 -> S2. S2(15MB) < 20MB, successful.
        - The best solution should be S2.
        """
        logging.info("\n--- Running test_compression_success_progressive ---")
        target_size = 20.0
        status, details = strategy.run_compression_strategy(self.input_pdf, self.test_dir, target_size)

        self.assertEqual(status, 'SUCCESS')
        self.assertEqual(details['best_scheme_id'], 2) # S2 is the first successful scheme
        self.assertIn('final_path', details)
        self.assertTrue(Path(details['final_path']).exists())

    def test_compression_failure(self):
        """
        Test failure scenario:
        - Target size: 0.5MB
        - Expectation: All solutions cannot meet the size and eventually fail.
        """
        logging.info("\n--- Running test_compression_failure ---")
        target_size = 0.5
        status, details = strategy.run_compression_strategy(self.input_pdf, self.test_dir, target_size)

        self.assertEqual(status, 'FAILURE')
        self.assertIn('all_results', details)
        self.assertEqual(len(details['all_results']), 6) # Should contain the trial results of all 6 solutions

    def test_file_already_small_enough(self):
        """
        Test the scenario where the file itself is already smaller than the target size.
        """
        logging.info("\n--- Running test_file_already_small_enough ---")
        # Simulate the original file size to be 1MB
        utils.get_file_size_mb = lambda x: 1.0 if x == self.input_pdf else fake_get_file_size_mb(x)
        
        target_size = 2.0
        status, details = strategy.run_compression_strategy(self.input_pdf, self.test_dir, target_size)

        self.assertEqual(status, 'SKIPPED')
        self.assertIn('message', details)

if __name__ == '__main__':
    unittest.main()
