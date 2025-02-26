import sys
import os
import json
from services.pdf_extraction import extract_prayer_times_from_pdf
from utils.logging_config import configure_logging
import logging

def main():
    # Configure logging
    log_file = configure_logging()
    logger = logging.getLogger(__name__)
    
    # Check command line arguments
    if len(sys.argv) < 3:
        logger.error("Usage: python extract_and_log.py <pdf_path> <year>")
        return
    
    pdf_path = sys.argv[1]
    year = sys.argv[2]
    
    logger.info(f"Starting extraction for PDF: {pdf_path}, Year: {year}")
    
    # Check if PDF exists
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return
    
    try:
        # Extract data from PDF
        data = extract_prayer_times_from_pdf(pdf_path, year)
        
        # Save extracted data to JSON for inspection
        output_file = f"extracted_data_{year}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({"year": year, "data": data}, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Extraction completed. Data saved to {output_file}")
        logger.info(f"Detailed logs saved to {log_file}")
        
    except Exception as e:
        logger.error(f"Extraction failed: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main() 