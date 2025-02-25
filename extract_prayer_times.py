import os
from flask import Flask, jsonify, abort
import pdfplumber
import re

app = Flask(__name__)

def extract_times(text):
    # Look for time strings such as "05:21" or "5:21"
    pattern = r'\b\d{1,2}:\d{2}\b'
    return re.findall(pattern, text)

def extract_prayer_times_from_page(text):
    # Simplified extraction: find all time strings on the page.
    times = extract_times(text)
    return times

def extract_all_prayer_times(pdf_path):
    extracted_data = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                times = extract_prayer_times_from_page(text)
                if times:
                    extracted_data.append({
                        "page": page_num,
                        "prayer_times": times
                    })
    return extracted_data

@app.route("/api/takvimi/<year>.json", methods=["GET"])
def get_takvimi_by_year(year):
    # Build file path assuming PDF files are in the "takvimi-pdf" folder
    pdf_filename = f"takvimi{year}.pdf"
    pdf_path = os.path.join("takvimi-pdf", pdf_filename)
    if not os.path.exists(pdf_path):
        abort(404, description="PDF file not found for the given year.")
    data = extract_all_prayer_times(pdf_path)
    return jsonify({
        "year": year,
        "data": data
    })

@app.route("/api/takvimi", methods=["GET"])
def list_available_pdfs():
    folder = "takvimi-pdf"
    if not os.path.exists(folder):
        abort(404, description="takvimi-pdf folder not found.")
    pdf_files = [f for f in os.listdir(folder) if f.endswith(".pdf")]
    return jsonify({
        "available_files": pdf_files
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
