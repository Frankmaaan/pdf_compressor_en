# compressor/strategy.py

import logging
import tempfile
from pathlib import Path
from . import utils, pipeline

# Define 7 compression schemes from S1 (the most conservative) to S7 (the most aggressive)
# The solution design takes into account the combination of DPI, background downsampling and JPEG2000 encoder
# S7 is the ultimate solution for exploring the limits of compression
COMPRESSION_SCHEMES = {
    1: {'name': 'S1-conservative', 'dpi': 300, 'bg_downsample': 2, 'jpeg2000_encoder': 'openjpeg'},
    2: {'name': 'S2-mild', 'dpi': 300, 'bg_downsample': 3, 'jpeg2000_encoder': 'grok'},
    3: {'name': 'S3-balanced', 'dpi': 250, 'bg_downsample': 3, 'jpeg2000_encoder': 'openjpeg'},
    4: {'name': 'S4-Enterprise', 'dpi': 200, 'bg_downsample': 4, 'jpeg2000_encoder': 'grok'},
    5: {'name': 'S5-Radical', 'dpi': 150, 'bg_downsample': 5, 'jpeg2000_encoder': 'openjpeg'},
    6: {'name': 'S6-limit', 'dpi': 100, 'bg_downsample': 8, 'jpeg2000_encoder': 'grok'},
    7: {'name': 'S7-Ultimate', 'dpi': 72, 'bg_downsample': 10, 'jpeg2000_encoder': 'grok'},
}

def _precompute_dar_steps(input_pdf_path, temp_dir):
    """
    Perform a one-time deconstruction and analysis step.
    """
    try:
        # Use S1's DPI for deconstruction as it is the highest quality
        dpi_for_deconstruct = COMPRESSION_SCHEMES[1]['dpi']
        logging.info(f"Deconstructing PDF with DPI: {dpi_for_deconstruct}")
        image_files = pipeline.deconstruct_pdf_to_images(input_pdf_path, temp_dir, dpi=dpi_for_deconstruct)
        if not image_files:
            logging.error("Preprocessing failed: Failed to extract images from PDF.")
            return None
        
        logging.info("Analyzing images to generate hOCR...")
        hocr_file = pipeline.analyze_images_to_hocr(image_files, temp_dir)
        if not hocr_file:
            logging.error("Preprocessing failed: Failed to generate hOCR file.")
            return None
            
        return {'image_files': image_files, 'hocr_file': hocr_file}
    except Exception as e:
        logging.error(f"An error occurred in the preprocessing step: {e}", exc_info=True)
        return None

def run_compression_strategy(input_pdf_path, output_dir, target_size_mb, keep_temp_on_failure=False):
    """
    Runs the new binary bidirectional search compression strategy.
    Returns a status tuple (status, details).
    status: 'SUCCESS', 'FAILURE', 'SKIPPED', 'ERROR'
    details: dictionary containing result information
    """
    original_size_mb = utils.get_file_size_mb(input_pdf_path)
    logging.info(f"File {input_pdf_path.name} (size: {original_size_mb:.2f}MB) applies new compression policy...")

    if original_size_mb < target_size_mb:
        logging.warning(f"The file {input_pdf_path.name} ({original_size_mb:.2f}MB) has met the requirements, skipping compression.")
        return 'SKIPPED', {'message': 'File size is already within target.'}

    temp_dir = Path(utils.create_temp_directory())
    
    try:
        # Precomputation step: only perform the most time-consuming deconstruction and analysis once
        logging.info(f"Preprocessing: Use the highest DPI ({COMPRESSION_SCHEMES[1]['dpi']}) to generate images and hOCR files...")
        precomputed_data = _precompute_dar_steps(input_pdf_path, temp_dir)
        if not precomputed_data:
            return 'ERROR', {'message': 'Preprocessing (DAR) failed.'}

        # Run core strategy logic
        final_result_path, all_results = _run_strategy_logic(
            input_pdf_path, output_dir, target_size_mb, temp_dir, precomputed_data
        )

        if final_result_path:
            best_scheme_id = final_result_path['scheme_id']
            final_path = final_result_path['path']
            return 'SUCCESS', {
                'best_scheme_id': best_scheme_id,
                'final_path': final_path,
                'all_results': all_results
            }
        else:
            return 'FAILURE', {'all_results': all_results}

    except Exception as e:
        logging.critical(f"Unexpected error occurred during compression policy execution: {e}", exc_info=True)
        return 'ERROR', {'message': str(e), 'all_results': {}}
    finally:
        if keep_temp_on_failure and 'final_result_path' not in locals():
             logging.warning(f"Compression failed, temporary directory remains in: {temp_dir}")
        else:
            utils.cleanup_directory(temp_dir)

def _run_strategy_logic(input_pdf_path, output_dir, target_size_mb, temp_dir, precomputed_data):
    """
    Internal functions that contain core compression policy logic.
    Return (final_result_path_dict, all_results) or (None, all_results)
    """
    all_results = {}

    # Step 1: Always execute the most conservative plan S1 first
    logging.info("--- Step 1: Execute the most conservative solution S1 ---")
    s1_result_path = _execute_scheme(1, temp_dir, precomputed_data, input_pdf_path.name)
    if not s1_result_path:
        logging.error("Key error: The execution of plan S1 failed and cannot continue.")
        return None, all_results
    
    s1_size_mb = utils.get_file_size_mb(s1_result_path)
    all_results[1] = {'path': s1_result_path, 'size_mb': s1_size_mb}

    # Check if S1 has met the requirements
    if s1_size_mb <= target_size_mb:
        logging.info(f"Great! The most conservative solution S1 has met the requirements (size: {s1_size_mb:.2f}MB).")
        return _copy_to_output(1, all_results, output_dir, input_pdf_path.name), all_results
    
    #Determine the next strategy based on the results of S1
    try:
        # If the result of S1 is greater than 1.5 times the target size, start the "jump-backtracking" strategy
        if s1_size_mb > target_size_mb * 1.5:
            logging.info(f"S1 result ({s1_size_mb:.2f}MB) > threshold ({target_size_mb * 1.5:.2f}MB), start [jump-backtracking] strategy.")
            
            # Step 2.1: Directly try the most radical solution S7
            logging.info("--- Step 2.1: Execute the most radical solution S7 ---")
            s7_result_path = _execute_scheme(7, temp_dir, precomputed_data, input_pdf_path.name)
            if s7_result_path:
                s7_size_mb = utils.get_file_size_mb(s7_result_path)
                all_results[7] = {'path': s7_result_path, 'size_mb': s7_size_mb}
                
                # Key check: If the S7 result is larger than 8MB, it means that it cannot be split and it will fail directly.
                if s7_size_mb > 8.0:
                    logging.error(f"❌ The result of the most aggressive scenario S7 ({s7_size_mb:.2f}MB) is still larger than the 8MB split threshold. Even if it is split, it cannot meet the 2MB target and the task fails.")
                    return None, all_results
                
                # If the S7 result is between 2MB and 8MB, the switching target is 8MB (prepared for splitting)
                if target_size_mb < 8.0 and s7_size_mb > target_size_mb:
                    logging.warning(f"⚠️ S7 result ({s7_size_mb:.2f}MB) exceeds original target ({target_size_mb:.2f}MB) but is less than 8MB.")
                    logging.info("🔄 Strategy adjustment: Switch the target to 8MB and find the solution closest to 8MB for subsequent splitting.")
                    target_size_mb = 8.0
                
                if s7_size_mb <= target_size_mb:
                    # S7 is successful, start backtracking to find higher quality solutions
                    logging.info("--- Step 2.2: Backtrack and search for higher quality solutions ---")
                    best_scheme_id = 7
                    # Trace upward from S6 to S2
                    for i in range(6, 1, -1):
                        result_path = _execute_scheme(i, temp_dir, precomputed_data, input_pdf_path.name)
                        if result_path:
                            size_mb = utils.get_file_size_mb(result_path)
                            all_results[i] = {'path': result_path, 'size_mb': size_mb}
                            if size_mb <= target_size_mb:
                                best_scheme_id = i # Update to the current better solution
                                logging.info(f"Scheme {COMPRESSION_SCHEMES[i]['name']} successful, size {size_mb:.2f}MB, continue to trace back...")
                            else:
                                logging.info(f"The scheme {COMPRESSION_SCHEMES[i]['name']} exceeds the target, select the previous scheme {COMPRESSION_SCHEMES[best_scheme_id]['name']} as the optimal solution.")
                                break # The current solution fails, stop backtracking
                    
                    logging.info(f"Backtracking completed, scheme {COMPRESSION_SCHEMES[best_scheme_id]['name']} is the highest quality scheme that can meet the goal.")
                    return _copy_to_output(best_scheme_id, all_results, output_dir, input_pdf_path.name), all_results

            # If S7 fails or is not executed, try S2 to S6 in order
            logging.warning("The S7 solution was not successful or not executed, the remaining solutions will be tried in order...")
            for i in range(2, 7):
                if i not in all_results:
                    result_path = _execute_scheme(i, temp_dir, precomputed_data, input_pdf_path.name)
                    if result_path:
                        size_mb = utils.get_file_size_mb(result_path)
                        all_results[i] = {'path': result_path, 'size_mb': size_mb}
                        if size_mb <= target_size_mb:
                            logging.info(f"Success! Scheme {COMPRESSION_SCHEMES[i]['name']} meets the requirements.")
                            # In this case, we found a feasible solution, but not through backtracking, so we return directly
                            return _copy_to_output(i, all_results, output_dir, input_pdf_path.name), all_results
            
            logging.error("All compression schemes failed.")
            return None, all_results

        # If the result of S1 is within 1.5 times the target size, start the "progressive" strategy
        else:
            logging.info(f"S1 result ({s1_size_mb:.2f}MB) <= threshold ({target_size_mb * 1.5:.2f}MB), start [progressive compression] strategy.")
            # Execute sequentially from S2 to S7 until the first one that meets the conditions is found
            for i in range(2, 8):
                result_path = _execute_scheme(i, temp_dir, precomputed_data, input_pdf_path.name)
                if result_path:
                    size_mb = utils.get_file_size_mb(result_path)
                    all_results[i] = {'path': result_path, 'size_mb': size_mb}
                    if size_mb <= target_size_mb:
                        logging.info(f"Success! Scheme {COMPRESSION_SCHEMES[i]['name']} meets the requirements.")
                        return _copy_to_output(i, all_results, output_dir, input_pdf_path.name), all_results
            
            logging.error("All progressive compression schemes failed.")
            return None, all_results
    except Exception as e:
        logging.critical(f"An unexpected error occurred during the execution of compression policy logic: {e}", exc_info=True)
        return None, all_results

def _copy_to_output(scheme_id, all_results, output_dir, original_filename):
    """Copy the final selected PDF to the output directory."""
    source_path = all_results[scheme_id]['path']
    output_filename = Path(original_filename).stem + "_compressed.pdf"
    dest_path = output_dir / output_filename
    
    try:
        utils.copy_file(source_path, dest_path)
        logging.info(f"File copied: {source_path} -> {dest_path}")
        return {'path': dest_path, 'scheme_id': scheme_id}
    except Exception as e:
        logging.error(f"Error copying final file: {e}")
        return None

def _execute_scheme(scheme_id, temp_dir, precomputed_data, original_filename):
    """
    Execute a single compression scheme.
    Now receives the precomputed_data dictionary.
    """
    scheme = COMPRESSION_SCHEMES[scheme_id]
    logging.info(f"--- Executing scheme {scheme['name']}: DPI={scheme['dpi']}, BG-Downsample={scheme['bg_downsample']}, Encoder={scheme['jpeg2000_encoder']} ---")
    
    output_pdf_path = temp_dir / f"output_{Path(original_filename).stem}_S{scheme_id}.pdf"
    
    params = {
        'name': scheme['name'],
        'dpi': scheme['dpi'],
        'bg_downsample': scheme['bg_downsample'],
        'jpeg2000_encoder': scheme['jpeg2000_encoder']
    }
    
    # S7 solution: Apply hOCR extreme optimization (remove text labels in exchange for smaller size)
    hocr_file_to_use = precomputed_data['hocr_file']
    if scheme_id == 7:
        logging.info("🔥 S7 extreme compression: apply hOCR optimization (will lose text search function but can reduce the size by about 7%)")
        # Create a copy to avoid affecting other solutions
        import shutil
        s7_hocr_file = temp_dir / "output_s7_optimized.hocr"
        shutil.copy2(precomputed_data['hocr_file'], s7_hocr_file)
        hocr_file_to_use = pipeline.optimize_hocr_for_extreme_compression(s7_hocr_file)

    try:
        success = pipeline.reconstruct_pdf(
            image_files=precomputed_data['image_files'],
            hocr_file=hocr_file_to_use,
            temp_dir=temp_dir,
            params=params,
            output_pdf_path=output_pdf_path
        )
        if success:
            return output_pdf_path
        else:
            logging.error(f"Scheme {scheme['name']} failed to reconstruct PDF.")
            return None
    except Exception as e:
        logging.error(f"An unexpected error occurred while executing scheme {scheme['name']}: {e}", exc_info=True)
        return None