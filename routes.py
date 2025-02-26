from flask import jsonify, abort, request, Response
import os
import json
import logging
import csv
import io
from services.pdf_extraction import extract_prayer_times_from_pdf, extract_page_as_csv
from services.data_manager import save_json_data, get_month_data

logger = logging.getLogger(__name__)

def register_routes(app):
    """Register all routes for the application"""
    
    @app.route("/api/takvimi/<year>.json", methods=["GET"])
    def get_takvimi_by_year(year):
        try:
            # Check if we should use cached data or not
            use_cache = request.args.get('use_cache', 'false').lower() == 'true'
            
            json_path = os.path.join(app.config['JSON_DIR'], f"{year}.json")
            
            # Only use cached data if explicitly requested and the file exists
            if use_cache and os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    return jsonify(json.load(f))
            
            # Otherwise, extract data from PDF
            pdf_filename = f"takvimi{year}.pdf"
            pdf_path = os.path.join(app.config['PDF_DIR'], pdf_filename)
            
            if not os.path.exists(pdf_path):
                abort(404, description=f"PDF file not found for the year {year}.")
                
            structured_data = extract_prayer_times_from_pdf(pdf_path, year)
            
            # If no data was extracted, return an appropriate message
            if not structured_data:
                return jsonify({
                    "year": year,
                    "data": {},
                    "message": "No data could be extracted from the PDF. The PDF format may not be supported."
                }), 200
            
            # Save the data to JSON files for future use
            save_json_data(year, structured_data)
            
            return jsonify({
                "year": year,
                "data": structured_data
            })
        except Exception as e:
            logger.error(f"Error processing request for year {year}: {str(e)}")
            abort(500, description=f"Error processing the PDF for year {year}.")

    @app.route("/api/takvimi/<year>/<month>.json", methods=["GET"])
    def get_takvimi_by_month(year, month):
        try:
            # Validate month format (should be 01-12)
            if not month.isdigit() or int(month) < 1 or int(month) > 12:
                abort(400, description="Month must be a number between 01 and 12.")
            
            # Ensure month is two digits
            month = month.zfill(2)
            
            # Check if we should use cached data or not
            use_cache = request.args.get('use_cache', 'true').lower() == 'true'
            
            # Try to get month data from cache first (faster path)
            if use_cache:
                month_data = get_month_data(year, month)
                if month_data:
                    return jsonify(month_data)
            
            # Check if full year data exists and extract month from it
            year_path = os.path.join(app.config['JSON_DIR'], f"{year}.json")
            if os.path.exists(year_path):
                with open(year_path, 'r', encoding='utf-8') as f:
                    year_data = json.load(f)
                    if 'data' in year_data and month in year_data['data']:
                        return jsonify({
                            "year": year,
                            "month": month,
                            "data": year_data['data'][month]
                        })
            
            # If not using cache or no cached data found, extract from PDF
            pdf_filename = f"takvimi{year}.pdf"
            pdf_path = os.path.join(app.config['PDF_DIR'], pdf_filename)
            
            if not os.path.exists(pdf_path):
                abort(404, description=f"PDF file not found for the year {year}.")
                
            structured_data = extract_prayer_times_from_pdf(pdf_path, year)
            
            # If no data was extracted, return an appropriate message
            if not structured_data:
                return jsonify({
                    "year": year,
                    "month": month,
                    "data": {},
                    "message": "No data could be extracted from the PDF. The PDF format may not be supported."
                }), 200
            
            # Save the data to JSON files for future use
            save_json_data(year, structured_data)
            
            # Return only the requested month's data
            if month in structured_data:
                return jsonify({
                    "year": year,
                    "month": month,
                    "data": structured_data[month]
                })
            else:
                return jsonify({
                    "year": year,
                    "month": month,
                    "data": {},
                    "message": f"No data found for month {month}."
                }), 404
        except Exception as e:
            logger.error(f"Error processing request for {year}-{month}: {str(e)}")
            abort(500, description=f"Error processing the PDF for {year}-{month}.")

    @app.route("/api/takvimi/<year>/page/<int:page_num>.csv", methods=["GET"])
    def get_pdf_page_as_csv(year, page_num):
        """Extract a specific page from the PDF as CSV"""
        try:
            # Always extract from PDF directly - no caching for CSV data
            pdf_filename = f"takvimi{year}.pdf"
            pdf_path = os.path.join(app.config['PDF_DIR'], pdf_filename)
            
            if not os.path.exists(pdf_path):
                abort(404, description=f"PDF file not found for the year {year}.")
            
            # Extract the page as CSV
            csv_data, error_message = extract_page_as_csv(pdf_path, page_num - 1)
            
            if not csv_data:
                return jsonify({
                    "error": "No data could be extracted from the page",
                    "message": error_message
                }), 404
            
            # Create a response with CSV data
            output = io.StringIO()
            writer = csv.writer(output)
            for row in csv_data:
                writer.writerow([str(cell).strip() if cell is not None else "" for cell in row])
            
            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={"Content-Disposition": f"attachment;filename=takvimi{year}_page{page_num}.csv"}
            )
        except Exception as e:
            logger.error(f"Error extracting page {page_num} from PDF: {str(e)}")
            abort(500, description=f"Error extracting page {page_num} from PDF: {str(e)}")

    @app.route("/api/takvimi", methods=["GET"])
    def list_available_pdfs():
        try:
            folder = app.config['PDF_DIR']
            json_dir = app.config['JSON_DIR']
            
            if not os.path.exists(folder):
                abort(404, description="takvimi-pdf folder not found.")
                
            pdf_files = [f for f in os.listdir(folder) if f.endswith(".pdf")]
            years = [f.replace("takvimi", "").replace(".pdf", "") for f in pdf_files]
            
            # Check for already processed JSON files
            json_files = [f for f in os.listdir(json_dir) if f.endswith(".json")]
            processed_years = [f.replace(".json", "") for f in json_files]
            
            # Check for processed months
            processed_months = {}
            for year in processed_years:
                year_dir = os.path.join(json_dir, year)
                if os.path.isdir(year_dir):
                    month_files = [f for f in os.listdir(year_dir) if f.endswith(".json")]
                    processed_months[year] = [f.replace(".json", "") for f in month_files]
            
            return jsonify({
                "available_years": years,
                "processed_years": processed_years,
                "processed_months": processed_months,
                "available_files": pdf_files,
                "caching_info": "By default, caching is enabled for month data and disabled for full year data. To change this behavior, add ?use_cache=true or ?use_cache=false to your request."
            })
        except Exception as e:
            logger.error(f"Error listing available PDFs: {str(e)}")
            abort(500, description="Error listing available PDF files.")

    @app.route("/", methods=["GET"])
    def home():
        return jsonify({
            "name": "Takvimi Shqip API",
            "description": "API for Albanian Islamic Calendar (Takvimi)",
            "endpoints": [
                "/api/takvimi - List available calendar years",
                "/api/takvimi/<year>.json - Get calendar data for specific year",
                "/api/takvimi/<year>/<month>.json - Get calendar data for specific month",
                "/api/takvimi/<year>/page/<page_num>.csv - Extract a specific page as CSV"
            ],
            "caching_behavior": "By default, caching is enabled for month data and disabled for full year data. To change this behavior, add ?use_cache=true or ?use_cache=false to your request."
        }) 