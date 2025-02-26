import os
import json
import logging
from config import JSON_DIR

logger = logging.getLogger(__name__)

def save_json_data(year, data):
    """Save the extracted data to JSON files - one for the full year and one for each month"""
    try:
        # Create year directory if it doesn't exist
        year_dir = os.path.join(JSON_DIR, year)
        os.makedirs(year_dir, exist_ok=True)
        
        # Save full year data
        json_path = os.path.join(JSON_DIR, f"{year}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({"year": year, "data": data}, f, ensure_ascii=False, indent=2)
        
        # Save individual month data
        for month, month_data in data.items():
            if month_data:  # Only save if there's data for this month
                month_path = os.path.join(year_dir, f"{month}.json")
                with open(month_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        "year": year,
                        "month": month,
                        "data": month_data
                    }, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        logger.error(f"Error saving JSON data: {str(e)}")
        return False

def get_month_data(year, month):
    """Get data for a specific month from its JSON file"""
    try:
        month_path = os.path.join(JSON_DIR, year, f"{month}.json")
        if os.path.exists(month_path):
            with open(month_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Error reading month data: {str(e)}")
        return None 