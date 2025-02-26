import pdfplumber
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

def extract_prayer_times_from_pdf(pdf_path, year):
    """
    Extracts prayer times from a PDF file specifically formatted for Albanian Islamic Calendar (Takvimi).
    This function is tailored to the specific format of the takvimi PDF.
    This version extracts data for all 12 months of the year with minimal logging for better performance.
    """
    # Initialize data structure for all months
    data = {
        '01': {}, '02': {}, '03': {}, '04': {}, 
        '05': {}, '06': {}, '07': {}, '08': {}, 
        '09': {}, '10': {}, '11': {}, '12': {}
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Process each month (January through December)
            all_months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
            for month_index, month_num in enumerate(all_months):
                # Calculate page indices for this month
                # January starts at pages 8-9, February at 10-11, etc.
                festival_page_index = 7 + (month_index * 2)  # 0-indexed, so page 8 is at index 7
                prayer_times_page_index = 8 + (month_index * 2)  # 0-indexed, so page 9 is at index 8
                
                # Ensure we don't go beyond the PDF
                if festival_page_index >= len(pdf.pages) or prayer_times_page_index >= len(pdf.pages):
                    continue
                
                # Extract festivals for this month
                festivals = {}
                extract_festivals(pdf.pages[festival_page_index], festivals)
                
                # Extract prayer times for this month
                extract_month_data(pdf.pages[prayer_times_page_index], data, festivals, month_num, year)
            
            # If we still have empty months, try a more aggressive approach
            empty_months = [m for m in all_months if len(data[m]) == 0]
            if empty_months:
                # Try to find tables on all pages
                for i in range(len(pdf.pages)):
                    page = pdf.pages[i]
                    tables = page.extract_tables()
                    
                    if not tables:
                        continue
                    
                    # Try to determine which month this page might be for
                    page_text = page.extract_text() or ""
                    month_detected = None
                    
                    # Check for month names in the text
                    month_patterns = [
                        ('janar', '01'), ('shkurt', '02'), ('mars', '03'), ('prill', '04'),
                        ('maj', '05'), ('qershor', '06'), ('korrik', '07'), ('gusht', '08'),
                        ('shtator', '09'), ('tetor', '10'), ('nëntor', '11'), ('dhjetor', '12')
                    ]
                    
                    for month_name, month_code in month_patterns:
                        if re.search(r'\b' + month_name + r'\b', page_text.lower()):
                            month_detected = month_code
                            break
                    
                    if not month_detected or month_detected not in empty_months:
                        continue
                    
                    # Process each table on this page
                    for table in tables:
                        if not table or len(table) <= 1:
                            continue
                        
                        # Try to extract data from this table
                        extract_from_table(table, data, month_detected, year)
    
    except Exception as e:
        logger.error(f"Error extracting data from PDF: {str(e)}")
        raise
    
    return data

def extract_festivals(page, festivals):
    """Extract festival information for a specific month"""
    try:
        # Extract tables from the page
        tables = page.extract_tables()
        if not tables:
            return
        
        # Process each table looking for festival information
        for table in tables:
            if not table or len(table) <= 1:
                continue
            
            # Process each row in the table (skip header)
            for row in table[1:]:  # Skip header row
                if not row or len(row) < 4:  # Need at least 4 columns for festivals
                    continue
                
                # Check if this row has a day number
                day_str = ""
                if row[0]:
                    # Try to extract a number from the first column
                    day_match = re.search(r'(\d+)', str(row[0]))
                    if day_match:
                        day_str = day_match.group(1)
                
                if not day_str:
                    continue
                
                # Extract festival information from column 4
                festival = row[3].strip() if len(row) > 3 and row[3] else ""
                
                if festival:
                    festivals[day_str] = festival
    
    except Exception as e:
        logger.error(f"Error extracting festivals: {str(e)}")

def extract_month_data(page, data, festivals, month_num, year):
    """Extract prayer times for a full month"""
    try:
        # Extract tables from the page
        tables = page.extract_tables()
        if not tables:
            return
        
        # Get the maximum number of days for this month
        max_days = 31  # Default for most months
        if month_num == '02':
            # Check if it's a leap year
            max_days = 29 if (int(year) % 4 == 0 and int(year) % 100 != 0) or (int(year) % 400 == 0) else 28
        elif month_num in ['04', '06', '09', '11']:
            max_days = 30  # April, June, September, November have 30 days
        
        # Process each table looking for days 1-max_days
        for table in tables:
            if not table or len(table) <= 1:
                continue
            
            # Process each row in the table (skip header)
            for row in table[1:]:  # Skip header row
                if not row or len(row) < 7:  # Need at least 7 columns for prayer times
                    continue
                
                # Check if this row has a day number
                day_str = ""
                if row[0]:
                    # Try to extract a number from the first column
                    day_match = re.search(r'(\d+)', str(row[0]))
                    if day_match:
                        day_str = day_match.group(1)
                
                if not day_str:
                    continue
                
                # Convert to integer to check if it's a valid day for this month
                try:
                    day_num = int(day_str)
                    if day_num < 1 or day_num > max_days:
                        continue  # Skip days outside the valid range
                except ValueError:
                    continue  # Skip if not a valid number
                
                # Extract day of week
                dita = row[1].strip() if len(row) > 1 and row[1] else ""
                
                # Extract prayer times - use a more robust approach
                times = []
                for cell in row[2:]:  # Skip day number and day of week
                    if cell:
                        time_match = re.search(r'(\d{1,2}:\d{2})', str(cell))
                        if time_match:
                            times.append(time_match.group(1))
                
                # If we found at least 7 times, use them
                if len(times) >= 7:
                    imsak = times[0]
                    sabahu = times[1]
                    lindja = times[2]
                    dreka = times[3]
                    ikindia = times[4]
                    akshami = times[5]
                    jacia = times[6]
                    gjatesia = times[7] if len(times) > 7 else ""
                    
                    # Get festival information for this day
                    festival = festivals.get(day_str, "")
                    
                    # Special handling for specific dates
                    if month_num == '01' and day_str == '1':
                        festival = festival or f"Viti i Ri {year}"
                    
                    # Store the data for this day
                    day_padded = day_str.zfill(2)  # Pad with leading zero if needed
                    data[month_num][day_padded] = {
                        "data_sipas_kal_boteror": day_num,
                        "dita_javes": dita,
                        "festat_fetare_dhe_shenime_te_tjera_astronomike": festival,
                        "kohet": {
                            "imsaku": imsak,
                            "sabahu": sabahu,
                            "lindja_e_diellit": lindja,
                            "dreka": dreka,
                            "ikindia": ikindia,
                            "akshami": akshami,
                            "jacia": jacia,
                            "gjatesia_e_dites": gjatesia
                        }
                    }
    
    except Exception as e:
        logger.error(f"Error extracting data for month {month_num}: {str(e)}")

def extract_from_table(table, data, month_num, year):
    """Extract data from a table using a more aggressive approach"""
    try:
        # Skip if table is too small
        if len(table) <= 1:
            return
        
        # Try to identify column structure from headers
        headers = [str(h).lower() if h else "" for h in table[0]]
        
        # Look for day column
        day_col = -1
        for i, header in enumerate(headers):
            if "ditë" in header or "dite" in header or "day" in header or "data" in header:
                day_col = i
                break
        
        # If we couldn't find a day column, assume it's the first column
        if day_col == -1:
            day_col = 0
        
        # Process each row in the table (skip header)
        for row in table[1:]:
            if not row or len(row) < 5:  # Need at least a few columns
                continue
            
            # Try to extract a day number
            day_str = ""
            if day_col < len(row) and row[day_col]:
                day_match = re.search(r'(\d+)', str(row[day_col]))
                if day_match:
                    day_str = day_match.group(1)
            
            if not day_str:
                continue
            
            # Convert to integer to check if it's a valid day
            try:
                day_num = int(day_str)
                max_days = 31
                if month_num == '02':
                    max_days = 29 if (int(year) % 4 == 0 and int(year) % 100 != 0) or (int(year) % 400 == 0) else 28
                
                if day_num < 1 or day_num > max_days:
                    continue  # Skip days outside the valid range
            except ValueError:
                continue  # Skip if not a valid number
            
            # Extract all time patterns from the row
            times = []
            for cell in row:
                if cell:
                    # Find all time patterns in this cell
                    time_matches = re.findall(r'(\d{1,2}:\d{2})', str(cell))
                    times.extend(time_matches)
            
            # If we found at least 7 times, use them
            if len(times) >= 7:
                # Extract day of week (assume it's in column 1 or 2)
                dita = ""
                for i in range(1, min(3, len(row))):
                    if row[i] and isinstance(row[i], str) and not re.search(r'\d+:\d+', row[i]):
                        dita = row[i].strip()
                        break
                
                # Store the data for this day
                day_padded = day_str.zfill(2)  # Pad with leading zero if needed
                data[month_num][day_padded] = {
                    "data_sipas_kal_boteror": day_num,
                    "dita_javes": dita,
                    "festat_fetare_dhe_shenime_te_tjera_astronomike": "",
                    "kohet": {
                        "imsaku": times[0],
                        "sabahu": times[1],
                        "lindja_e_diellit": times[2],
                        "dreka": times[3],
                        "ikindia": times[4],
                        "akshami": times[5],
                        "jacia": times[6],
                        "gjatesia_e_dites": times[7] if len(times) > 7 else ""
                    }
                }
    
    except Exception as e:
        logger.error(f"Error in aggressive extraction: {str(e)}")

def count_days_with_prayer_times(data, month_num):
    """Count how many days in a month have prayer times"""
    if month_num not in data:
        return 0
    
    count = 0
    for day, day_data in data[month_num].items():
        if "kohet" in day_data and day_data["kohet"]["imsaku"]:
            count += 1
    
    return count

def extract_festivals_for_month(page, data, month_num, year):
    """Extract festival information for a specific month"""
    try:
        logger.info(f"Extracting festivals for month {month_num}")
        
        # Extract text from the page
        text = page.extract_text()
        if not text:
            logger.warning(f"No text found on festival page for month {month_num}")
            return
        
        # Extract tables from the page
        tables = page.extract_tables()
        if not tables:
            logger.warning(f"No tables found on festival page for month {month_num}")
            return
        
        # Process each table
        for table in tables:
            if not table or len(table) <= 1:
                continue
            
            # Process each row in the table
            for row in table:
                if not row or len(row) < 4:  # Need at least 4 columns
                    continue
                
                # First column should be a day number
                day_str = row[0].strip() if row[0] else ""
                if not day_str or not re.match(r'^\d+$', day_str):
                    continue
                
                # Extract festival information from column 4
                festival = row[3].strip() if len(row) > 3 and row[3] else ""
                
                # Store the festival information
                day = day_str.zfill(2)
                if month_num not in data:
                    data[month_num] = {}
                
                if day not in data[month_num]:
                    data[month_num][day] = {
                        "data_sipas_kal_boteror": int(day_str),
                        "dita_javes": "",  # Will be filled in later
                        "festat_fetare_dhe_shenime_te_tjera_astronomike": festival,
                        "kohet": {
                            "imsaku": "",
                            "sabahu": "",
                            "lindja_e_diellit": "",
                            "dreka": "",
                            "ikindia": "",
                            "akshami": "",
                            "jacia": "",
                            "gjatesia_e_dites": ""
                        }
                    }
                else:
                    # Update just the festival information
                    data[month_num][day]["festat_fetare_dhe_shenime_te_tjera_astronomike"] = festival
                
                logger.info(f"Extracted festival for {month_num}-{day}: {festival}")
    
    except Exception as e:
        logger.error(f"Error extracting festivals for month {month_num}: {str(e)}")

def extract_prayer_times_for_month(page, data, month_num, year):
    """Extract prayer times for a specific month"""
    try:
        logger.info(f"Extracting prayer times for month {month_num}")
        
        # Extract tables from the page
        tables = page.extract_tables()
        if not tables:
            logger.warning(f"No tables found on prayer times page for month {month_num}")
            return
        
        # Process each table
        for table in tables:
            if not table or len(table) <= 1:
                continue
            
            # Process each row in the table (skip header)
            for row_idx, row in enumerate(table[1:], 1):
                if not row or len(row) < 7:  # Need at least 7 columns for prayer times
                    continue
            
                # Try to extract day number from first column
                day_str = ""
                if row[0]:
                    # Try to extract a number from the first column
                    day_match = re.search(r'(\d+)', str(row[0]))
                    if day_match:
                        day_str = day_match.group(1)
                
                if not day_str:
                    continue
                
                # Extract day of week
                dita = row[1].strip() if len(row) > 1 and row[1] else ""
                
                # Extract prayer times - use a more robust approach
                times = []
                for cell in row[2:]:  # Skip day number and day of week
                    if cell:
                        time_match = re.search(r'(\d{1,2}:\d{2})', str(cell))
                        if time_match:
                            times.append(time_match.group(1))
                
                # If we found at least 7 times, use them
                if len(times) >= 7:
                    imsak = times[0]
                    sabahu = times[1]
                    lindja = times[2]
                    dreka = times[3]
                    ikindia = times[4]
                    akshami = times[5]
                    jacia = times[6]
                    gjatesia = times[7] if len(times) > 7 else ""
                    
                    # Store the data
                    day = day_str.zfill(2)
                if month_num not in data:
                    data[month_num] = {}
                
                if day not in data[month_num]:
                    # Create new entry
                    data[month_num][day] = {
                        "data_sipas_kal_boteror": int(day_str),
                        "dita_javes": dita,
                        "festat_fetare_dhe_shenime_te_tjera_astronomike": "",  # Will be filled from festival page
                        "kohet": {
                            "imsaku": imsak,
                            "sabahu": sabahu,
                            "lindja_e_diellit": lindja,
                            "dreka": dreka,
                            "ikindia": ikindia,
                            "akshami": akshami,
                            "jacia": jacia,
                            "gjatesia_e_dites": gjatesia
                        }
                    }
                else:
                    # Update existing entry
                    data[month_num][day]["dita_javes"] = dita
                    data[month_num][day]["kohet"] = {
                        "imsaku": imsak,
                        "sabahu": sabahu,
                        "lindja_e_diellit": lindja,
                        "dreka": dreka,
                        "ikindia": ikindia,
                        "akshami": akshami,
                        "jacia": jacia,
                        "gjatesia_e_dites": gjatesia
                    }
    
    except Exception as e:
        logger.error(f"Error extracting prayer times for month {month_num}: {str(e)}")

def extract_time(cell):
    """Extract a time pattern (HH:MM) from a cell"""
    if not cell:
        return ""
    
    cell_str = str(cell).strip()
    
    # If the cell already matches the time pattern, return it
    if re.match(r'^\d{1,2}:\d{2}$', cell_str):
        return cell_str
    
    # Otherwise, try to extract a time pattern from the text
    time_match = re.search(r'(\d{1,2}:\d{2})', cell_str)
    if time_match:
        return time_match.group(1)
    
    return ""

def extract_religious_holidays(pdf, data, year):
    """Extract religious holidays and astronomical notes from page 8"""
    try:
        # Page 8 contains the religious holidays
        if len(pdf.pages) >= 8:
            page = pdf.pages[7]  # 0-indexed, so page 8 is at index 7
            logger.info("Extracting religious holidays from page 8")
            
            text = page.extract_text()
            if not text:
                logger.warning("No text found on page 8")
                return
            
            # Extract tables from the page
            tables = page.extract_tables()
            if not tables:
                logger.warning("No tables found on page 8")
                return
            
            holidays = {}
            
            # Process each table
            for table in tables:
                if not table or len(table) <= 1:
                    continue
                
                # Process each row in the table
                for row in table[1:]:  # Skip header row
                    if not row or len(row) < 3:
                        continue
                    
                    # Extract date and holiday information
                    date_info = row[0].strip() if row[0] else ""
                    holiday_info = row[2].strip() if len(row) > 2 and row[2] else ""
                    
                    if not date_info or not holiday_info:
                        continue
                    
                    # Try to extract month and day from date_info
                    date_match = re.search(r'(\d+)\s+([A-Za-zëË]+)', date_info)
                    if date_match:
                        day = date_match.group(1).zfill(2)
                        month_name = date_match.group(2).lower()
                        
                        # Convert month name to number
                        month_map = {
                            'janar': '01', 'shkurt': '02', 'mars': '03', 'prill': '04',
                            'maj': '05', 'qershor': '06', 'korrik': '07', 'gusht': '08',
                            'shtator': '09', 'tetor': '10', 'nëntor': '11', 'dhjetor': '12'
                        }
                        month = month_map.get(month_name)
                        
                        if month and day:
                            key = f"{month}-{day}"
                            holidays[key] = holiday_info
                            logger.info(f"Found holiday: {key} - {holiday_info}")
            
            # Store the holidays for later use when processing prayer times
            return holidays
    except Exception as e:
        logger.error(f"Error extracting religious holidays: {str(e)}")
    return {}

def extract_prayer_times(pdf, data, year):
    """Extract prayer times from all pages of the PDF"""
    # Process each page
    for page_num, page in enumerate(pdf.pages):
        logger.info(f"Processing page {page_num+1}")
        
        # Extract text from the page
        text = page.extract_text()
        if not text:
            logger.warning(f"No text found on page {page_num+1}")
            continue
        
        # Split the text into lines
        lines = text.split('\n')
        logger.info(f"Found {len(lines)} lines of text on page {page_num+1}")
        
        # Special handling for January (page 9)
        if page_num == 8:  # 0-indexed, so page 9 is at index 8
            logger.info("Processing January prayer times from page 9")
            extract_january_prayer_times(page, data, year)
            continue
        
        # For other pages, use the regular extraction method
        current_month = detect_month_from_page(page, page_num)
        if not current_month:
            continue
        
        # Process each line for prayer times
        for line in lines:
            # Skip lines that don't contain prayer times
            if not re.search(r'\d+:\d+', line):
                continue
            
            # Try multiple patterns to match different formats
            process_prayer_time_line(line, data, current_month, year)

def extract_january_prayer_times(page, data, month_num, year):
    """Extract prayer times using the January-specific method, but for any month"""
    if month_num not in data:
        data[month_num] = {}
    
    # Extract tables from the page
    tables = page.extract_tables()
    if not tables:
        logger.warning(f"No tables found on prayer times page for month {month_num}")
        return
    
    # Process each table
    for table in tables:
        if not table or len(table) <= 1:
            continue
        
        # Check if this is the prayer times table
        header_row = table[0]
        if not header_row:
            continue
        
        # Look for column headers that indicate this is the prayer times table
        # Use a more flexible approach
        header_text = " ".join([str(cell) for cell in header_row if cell])
        
        # More flexible pattern matching for prayer time headers
        if not (re.search(r'imsak', header_text, re.IGNORECASE) or 
                re.search(r'sabah', header_text, re.IGNORECASE) or
                re.search(r'dreka', header_text, re.IGNORECASE) or
                re.search(r'ikindia', header_text, re.IGNORECASE) or
                re.search(r'akshami', header_text, re.IGNORECASE) or
                re.search(r'jacia', header_text, re.IGNORECASE)):
            continue
        
        logger.info(f"Found prayer times table for month {month_num}")
        
        # Process each row in the table
        for row in table[1:]:  # Skip header row
            if not row:
                continue
            
            # Extract day number - be more flexible
            kal_bot = ""
            if row[0]:
                # Try to extract a number from the first column
                day_match = re.search(r'(\d+)', str(row[0]))
                if day_match:
                    kal_bot = day_match.group(1)
            
            if not kal_bot:
                continue
            
            # Extract other data based on the actual number of columns
            dita = row[1].strip() if len(row) > 1 and row[1] else ""
            
            # For religious holidays, we'll use the known holidays from corrections.py
            fest = ""
            
            # Find columns that contain time patterns (HH:MM)
            time_columns = []
            for i, cell in enumerate(row):
                if cell and re.search(r'\d{1,2}:\d{2}', str(cell)):
                    time_columns.append(i)
            
            # If we found at least 7 time columns, extract the prayer times
            if len(time_columns) >= 7:
                imsak = extract_time(row[time_columns[0]])
                sabahu = extract_time(row[time_columns[1]])
                lindja = extract_time(row[time_columns[2]])
                dreka = extract_time(row[time_columns[3]])
                ikindia = extract_time(row[time_columns[4]])
                akshami = extract_time(row[time_columns[5]])
                jacia = extract_time(row[time_columns[6]])
                
                # Get day length from the last time column if available
                gjatesia = extract_time(row[time_columns[-1]]) if len(time_columns) > 7 else ""
            else:
                # Fallback to fixed column indices
                col_offset = 3  # Starting column for prayer times
            
                imsak = extract_time(row[col_offset]) if len(row) > col_offset else ""
                sabahu = extract_time(row[col_offset+1]) if len(row) > col_offset+1 else ""
                lindja = extract_time(row[col_offset+2]) if len(row) > col_offset+2 else ""
                dreka = extract_time(row[col_offset+3]) if len(row) > col_offset+3 else ""
                ikindia = extract_time(row[col_offset+4]) if len(row) > col_offset+4 else ""
                akshami = extract_time(row[col_offset+5]) if len(row) > col_offset+5 else ""
                jacia = extract_time(row[col_offset+6]) if len(row) > col_offset+6 else ""
            
            # Get day length from the last column
                gjatesia = extract_time(row[-1]) if len(row) > col_offset+7 else ""
            
            logger.info(f"{month_num} day {kal_bot}: imsak={imsak}, sabahu={sabahu}")
            
            # Process and store the data
            process_prayer_time(data, month_num, kal_bot, dita, "0", fest, 
                               imsak, sabahu, lindja, dreka, ikindia, akshami, 
                               jacia, gjatesia, year, "flexible_extraction")

def detect_month_from_page(page, page_num):
    """Detect which month is represented on this page"""
    text = page.extract_text()
    if not text:
        return None
    
    # Look for month names in the text
    for month_name, month_num in [
        ('janar', '01'), ('shkurt', '02'), ('mars', '03'), ('prill', '04'),
        ('maj', '05'), ('qershor', '06'), ('korrik', '07'), ('gusht', '08'),
        ('shtator', '09'), ('tetor', '10'), ('nëntor', '11'), ('dhjetor', '12')
    ]:
        if re.search(r'\b' + month_name + r'\b', text, re.IGNORECASE):
            logger.info(f"Found month: {month_name} ({month_num}) on page {page_num+1}")
            return month_num
    
    # If we couldn't determine the month, try to infer it from the page number
    if page_num < 12:
        # Assume pages are in order of months
        inferred_month = str(page_num + 1).zfill(2)
        if 1 <= int(inferred_month) <= 12:
            logger.info(f"Inferred month from page number: {inferred_month}")
            return inferred_month
    
    return None

def process_prayer_time_line(line, data, current_month, year):
    """Process a line of text to extract prayer times"""
    # Pattern 1: Standard format with all fields
    pattern1 = r'(\d+)\s+([^\s]+)\s+(\d+)\s+(.*?)\s+(\d+:\d+)\s+(\d+:\d+)\s+(\d+:\d+)\s+(\d+:\d+)\s+(\d+:\d+)\s+(\d+:\d+)\s+(\d+:\d+)\s+(\d+:\d+)'
    match1 = re.search(pattern1, line)
    
    # Pattern 2: Alternative format with fewer fields
    pattern2 = r'(\d+)[^\d]+(\d+)[^\d]+(.*?)(\d{1,2}:\d{2})\s+(\d{1,2}:\d{2})\s+(\d{1,2}:\d{2})\s+(\d{1,2}:\d{2})\s+(\d{1,2}:\d{2})\s+(\d{1,2}:\d{2})\s+(\d{1,2}:\d{2})'
    match2 = re.search(pattern2, line)
    
    # Pattern 3: Simpler pattern just looking for a day number followed by times
    pattern3 = r'^\s*(\d+)(?:\D+(\d+))?(?:\D+([^\d]*))?(?:\D+(\d{1,2}:\d{2}))?(?:\D+(\d{1,2}:\d{2}))?(?:\D+(\d{1,2}:\d{2}))?(?:\D+(\d{1,2}:\d{2}))?(?:\D+(\d{1,2}:\d{2}))?(?:\D+(\d{1,2}:\d{2}))?(?:\D+(\d{1,2}:\d{2}))?'
    match3 = re.search(pattern3, line)
    
    if match1:
        # Process standard format
        kal_bot = match1.group(1)
        dita = match1.group(2)
        takvim = match1.group(3)
        fest = match1.group(4).strip()
        imsak = match1.group(5)
        sabahu = match1.group(6)
        lindja = match1.group(7)
        dreka = match1.group(8)
        ikindia = match1.group(9)
        akshami = match1.group(10)
        jacia = match1.group(11)
        gjatesia = match1.group(12)
        
        process_prayer_time(data, current_month, kal_bot, dita, takvim, fest, 
                           imsak, sabahu, lindja, dreka, ikindia, akshami, 
                           jacia, gjatesia, year, "pattern1")
        
    elif match2:
        # Process alternative format
        kal_bot = match2.group(1)
        takvim = match2.group(2)
        
        # Try to determine the day of week based on the date
        try:
            date_obj = datetime.strptime(f"{year}-{current_month}-{kal_bot.zfill(2)}", "%Y-%m-%d")
            days_of_week = ["e hënë", "e martë", "e mërkurë", "e enjte", "e premte", "e shtunë", "e diel"]
            dita = days_of_week[date_obj.weekday()]
        except:
            dita = ""
        
        fest = match2.group(3).strip()
        imsak = match2.group(4)
        sabahu = match2.group(5)
        lindja = match2.group(6)
        dreka = match2.group(7)
        ikindia = match2.group(8)
        akshami = match2.group(9)
        
        # The last group might contain both jacia and gjatesia
        last_part = match2.group(10)
        jacia_match = re.search(r'(\d{1,2}:\d{2})', last_part)
        if jacia_match:
            jacia = jacia_match.group(1)
            # Try to find gjatesia after jacia
            gjatesia_match = re.search(r'(\d{1,2}:\d{2})', last_part[jacia_match.end():])
            gjatesia = gjatesia_match.group(1) if gjatesia_match else ""
        else:
            jacia = last_part
            gjatesia = ""
        
        process_prayer_time(data, current_month, kal_bot, dita, takvim, fest, 
                           imsak, sabahu, lindja, dreka, ikindia, akshami, 
                           jacia, gjatesia, year, "pattern2")
        
    elif match3:
        # Process simple format - this is a fallback for lines that don't match the other patterns
        kal_bot = match3.group(1)
        takvim = match3.group(2) if match3.group(2) else "0"
        fest = match3.group(3).strip() if match3.group(3) else ""
        
        # Try to determine the day of week based on the date
        try:
            date_obj = datetime.strptime(f"{year}-{current_month}-{kal_bot.zfill(2)}", "%Y-%m-%d")
            days_of_week = ["e hënë", "e martë", "e mërkurë", "e enjte", "e premte", "e shtunë", "e diel"]
            dita = days_of_week[date_obj.weekday()]
        except:
            dita = ""
        
        # Extract time values, using empty strings for missing values
        imsak = match3.group(4) if match3.group(4) else ""
        sabahu = match3.group(5) if match3.group(5) else ""
        lindja = match3.group(6) if match3.group(6) else ""
        dreka = match3.group(7) if match3.group(7) else ""
        ikindia = match3.group(8) if match3.group(8) else ""
        akshami = match3.group(9) if match3.group(9) else ""
        jacia = match3.group(10) if match3.group(10) else ""
        gjatesia = match3.group(11) if match3.group(11) else ""
        
        process_prayer_time(data, current_month, kal_bot, dita, takvim, fest, 
                           imsak, sabahu, lindja, dreka, ikindia, akshami, 
                           jacia, gjatesia, year, "pattern3")
    
    # If none of the patterns matched, try a more aggressive approach
    else:
        # Extract all time patterns from the line
        time_patterns = re.findall(r'\d{1,2}:\d{2}', line)
        
        # If we have at least 7 time patterns and a day number, we can try to extract data
        day_match = re.search(r'^\s*(\d+)', line)
        if day_match and len(time_patterns) >= 7:
            kal_bot = day_match.group(1)
            
            # Try to determine the day of week based on the date
            try:
                date_obj = datetime.strptime(f"{year}-{current_month}-{kal_bot.zfill(2)}", "%Y-%m-%d")
                days_of_week = ["e hënë", "e martë", "e mërkurë", "e enjte", "e premte", "e shtunë", "e diel"]
                dita = days_of_week[date_obj.weekday()]
            except:
                dita = ""
            
            # Extract takvim (Islamic date) if present
            takvim_match = re.search(r'^\s*\d+\s+\S+\s+(\d+)', line)
            takvim = takvim_match.group(1) if takvim_match else "0"
            
            # Extract festival/notes if present
            fest = ""
            
            # Use the time patterns in order
            imsak = time_patterns[0] if len(time_patterns) > 0 else ""
            sabahu = time_patterns[1] if len(time_patterns) > 1 else ""
            lindja = time_patterns[2] if len(time_patterns) > 2 else ""
            dreka = time_patterns[3] if len(time_patterns) > 3 else ""
            ikindia = time_patterns[4] if len(time_patterns) > 4 else ""
            akshami = time_patterns[5] if len(time_patterns) > 5 else ""
            jacia = time_patterns[6] if len(time_patterns) > 6 else ""
            gjatesia = time_patterns[7] if len(time_patterns) > 7 else ""
            
            process_prayer_time(data, current_month, kal_bot, dita, takvim, fest, 
                               imsak, sabahu, lindja, dreka, ikindia, akshami, 
                               jacia, gjatesia, year, "fallback")

def process_prayer_time(data, month, kal_bot, dita, takvim, fest, 
                       imsak, sabahu, lindja, dreka, ikindia, akshami, 
                       jacia, gjatesia, year, pattern_name):
    """Helper function to process and store prayer time data"""
    try:
        day = kal_bot.zfill(2)
        
        if month not in data:
            data[month] = {}
        
        # Ensure fest is treated as text, not a number
        fest_text = fest.strip() if fest else ""
        
        # Check if this date has a known holiday
        date_key = f"{month}-{day}"
        known_holidays = get_known_holidays(year)
        if date_key in known_holidays:
            # If we already have some festival text, append the known holiday
            if fest_text:
                fest_text = f"{fest_text}, {known_holidays[date_key]}"
            else:
                fest_text = known_holidays[date_key]
            logger.info(f"Added known holiday for {date_key}: {known_holidays[date_key]}")
        
        # Apply time corrections if available
        full_date_key = f"{year}-{month}-{day}"
        time_corrections = get_time_corrections(year)
        
        if full_date_key in time_corrections:
            corrections = time_corrections[full_date_key]
            if "imsaku" in corrections:
                imsak = corrections["imsaku"]
                logger.info(f"Applied time correction for {full_date_key}: imsaku = {imsak}")
            if "sabahu" in corrections:
                sabahu = corrections["sabahu"]
                logger.info(f"Applied time correction for {full_date_key}: sabahu = {sabahu}")
            if "lindja_e_diellit" in corrections:
                lindja = corrections["lindja_e_diellit"]
                logger.info(f"Applied time correction for {full_date_key}: lindja_e_diellit = {lindja}")
            if "dreka" in corrections:
                dreka = corrections["dreka"]
                logger.info(f"Applied time correction for {full_date_key}: dreka = {dreka}")
            if "ikindia" in corrections:
                ikindia = corrections["ikindia"]
                logger.info(f"Applied time correction for {full_date_key}: ikindia = {ikindia}")
            if "akshami" in corrections:
                akshami = corrections["akshami"]
                logger.info(f"Applied time correction for {full_date_key}: akshami = {akshami}")
            if "jacia" in corrections:
                jacia = corrections["jacia"]
                logger.info(f"Applied time correction for {full_date_key}: jacia = {jacia}")
            if "gjatesia_e_dites" in corrections:
                gjatesia = corrections["gjatesia_e_dites"]
                logger.info(f"Applied time correction for {full_date_key}: gjatesia_e_dites = {gjatesia}")
        
        data[month][day] = {
            "data_sipas_kal_boteror": int(kal_bot),
            "dita_javes": dita,
            "festat_fetare_dhe_shenime_te_tjera_astronomike": fest_text,
            "kohet": {
                "imsaku": imsak,
                "sabahu": sabahu,
                "lindja_e_diellit": lindja,
                "dreka": dreka,
                "ikindia": ikindia,
                "akshami": akshami,
                "jacia": jacia,
                "gjatesia_e_dites": gjatesia
            }
        }
        logger.info(f"Successfully processed day {day} of month {month} using {pattern_name}")
        return True
    except Exception as e:
        logger.warning(f"Error processing prayer time: {str(e)}")
        return False

def extract_prayer_times_structured(pdf_path, year):
    """
    Extracts a table from the PDF and restructures each row into a nested dictionary.
    This is a fallback method if the specialized extraction fails.
    """
    data = {}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Try to determine which pages correspond to which months
            month_pages = {}
            
            # First pass: identify month headers on each page
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text()
                if not text:
                    continue
                
                for month_name, month_num in [
                    ('janar', '01'), ('shkurt', '02'), ('mars', '03'), ('prill', '04'),
                    ('maj', '05'), ('qershor', '06'), ('korrik', '07'), ('gusht', '08'),
                    ('shtator', '09'), ('tetor', '10'), ('nëntor', '11'), ('dhjetor', '12')
                ]:
                    if re.search(month_name, text, re.IGNORECASE):
                        if month_num not in month_pages:
                            month_pages[month_num] = []
                        month_pages[month_num].append(page_num)
            
            # Second pass: extract tables from each page
            for page_num, page in enumerate(pdf.pages):
                # Special handling for January (page 9)
                if page_num == 8:  # 0-indexed, so page 9 is at index 8
                    logger.info("Processing January prayer times from page 9 (structured)")
                    extract_january_prayer_times(page, data, year)
                    continue
                
                # Determine which month this page belongs to
                current_month = None
                for month, pages in month_pages.items():
                    if page_num in pages:
                        current_month = month
                        break
                
                # If we couldn't determine the month, try to infer it
                if not current_month:
                    # Simple heuristic: assume pages are in order of months
                    if page_num < 12:
                        current_month = str(page_num + 1).zfill(2)
                    else:
                        continue  # Skip if we can't determine the month
                
                tables = page.extract_tables()
                if not tables:
                    continue
                
                for table in tables:
                    if not table or len(table) <= 1:
                        continue
                    
                    # Assume first row is header; skip it
                    for row in table[1:]:
                        if not row or len(row) < 7:  # Minimum columns needed
                            continue
                        
                        # Clean and validate data
                        kal_bot = row[0].strip() if row[0] else ""
                        if not kal_bot or not re.match(r'^\d+$', kal_bot):
                            continue
                        
                        # Extract available data, using defaults for missing columns
                        dita = row[1].strip() if len(row) > 1 and row[1] else ""
                        takvim = row[2].strip() if len(row) > 2 and row[2] else "0"
                        fest = row[3].strip() if len(row) > 3 and row[3] else ""
                        
                        # Prayer times
                        imsak = row[4].strip() if len(row) > 4 and row[4] else ""
                        sabahu = row[5].strip() if len(row) > 5 and row[5] else ""
                        lindja = row[6].strip() if len(row) > 6 and row[6] else ""
                        dreka = row[7].strip() if len(row) > 7 and row[7] else ""
                        ikindia = row[8].strip() if len(row) > 8 and row[8] else ""
                        akshami = row[9].strip() if len(row) > 9 and row[9] else ""
                        jacia = row[10].strip() if len(row) > 10 and row[10] else ""
                        gjatesia = row[11].strip() if len(row) > 11 and row[11] else ""

                        day = kal_bot.zfill(2)
                        if current_month not in data:
                            data[current_month] = {}
                        
                        # Check if this date has a known holiday
                        date_key = f"{current_month}-{day}"
                        known_holidays = get_known_holidays(year)
                        if date_key in known_holidays:
                            # If we already have some festival text, append the known holiday
                            if fest:
                                fest = f"{fest}, {known_holidays[date_key]}"
                            else:
                                fest = known_holidays[date_key]
                            logger.info(f"Added known holiday for {date_key}: {known_holidays[date_key]}")
                        
                        # Apply time corrections if available
                        full_date_key = f"{year}-{current_month}-{day}"
                        time_corrections = get_time_corrections(year)
                        
                        if full_date_key in time_corrections:
                            corrections = time_corrections[full_date_key]
                            if "imsaku" in corrections:
                                imsak = corrections["imsaku"]
                            if "sabahu" in corrections:
                                sabahu = corrections["sabahu"]
                            if "lindja_e_diellit" in corrections:
                                lindja = corrections["lindja_e_diellit"]
                            if "dreka" in corrections:
                                dreka = corrections["dreka"]
                            if "ikindia" in corrections:
                                ikindia = corrections["ikindia"]
                            if "akshami" in corrections:
                                akshami = corrections["akshami"]
                            if "jacia" in corrections:
                                jacia = corrections["jacia"]
                            if "gjatesia_e_dites" in corrections:
                                gjatesia = corrections["gjatesia_e_dites"]
                            logger.info(f"Applied time corrections for {full_date_key}")
                        
                        try:
                            data[current_month][day] = {
                                "data_sipas_kal_boteror": int(kal_bot),
                                "dita_javes": dita,
                                "festat_fetare_dhe_shenime_te_tjera_astronomike": fest.strip() if fest else "",
                                "kohet": {
                                    "imsaku": imsak,
                                    "sabahu": sabahu,
                                    "lindja_e_diellit": lindja,
                                    "dreka": dreka,
                                    "ikindia": ikindia,
                                    "akshami": akshami,
                                    "jacia": jacia,
                                    "gjatesia_e_dites": gjatesia
                                }
                            }
                            logger.info(f"Successfully processed day {day} of month {current_month} using table extraction")
                        except ValueError as e:
                            logger.warning(f"Error processing row {row}: {str(e)}")
                            continue
    except Exception as e:
        logger.error(f"Error in structured extraction: {str(e)}") 

def extract_page_as_csv(pdf_path, page_index):
    """Extract a specific page from the PDF as CSV data"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if page_index < 0 or page_index >= len(pdf.pages):
                return None, "Invalid page number"
            
            # Get the specified page
            page = pdf.pages[page_index]
            
            # Extract tables from the page
            tables = page.extract_tables()
            if not tables:
                return None, page.extract_text() or "No tables found on this page"
            
            # Return the first table
            return tables[0], None
    
    except Exception as e:
        logger.error(f"Error extracting page as CSV: {str(e)}")
        return None, str(e) 