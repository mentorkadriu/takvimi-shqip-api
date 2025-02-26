import pdfplumber
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

def extract_prayer_times_from_pdf(pdf_path, year):
    """
    Extracts prayer times from a PDF file specifically formatted for Albanian Islamic Calendar (Takvimi).
    This function is tailored to the specific format of the takvimi PDF.
    """
    data = {}
    try:
        with pdfplumber.open(pdf_path) as pdf:
            logger.info(f"PDF opened successfully: {pdf_path}")
            logger.info(f"Number of pages: {len(pdf.pages)}")
            
            # Initialize current_month to handle cases where month header might be missing
            current_month = None
            
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
                
                # First, try to identify the month for this page
                for line in lines:
                    # More comprehensive month detection pattern
                    month_match = re.search(r'\b(Janar|Shkurt|Mars|Prill|Maj|Qershor|Korrik|Gusht|Shtator|Tetor|Nëntor|Dhjetor)\b', line, re.IGNORECASE)
                    if month_match:
                        month_name = month_match.group(1).lower()
                        # Convert month name to number
                        month_map = {
                            'janar': '01', 'shkurt': '02', 'mars': '03', 'prill': '04',
                            'maj': '05', 'qershor': '06', 'korrik': '07', 'gusht': '08',
                            'shtator': '09', 'tetor': '10', 'nëntor': '11', 'dhjetor': '12'
                        }
                        current_month = month_map.get(month_name)
                        if current_month:
                            logger.info(f"Found month: {month_name} ({current_month})")
                            if current_month not in data:
                                data[current_month] = {}
                
                # If we couldn't determine the month, try to infer it from the page number
                if not current_month and page_num < 12:
                    # Assume pages are in order of months
                    inferred_month = str(page_num + 1).zfill(2)
                    if 1 <= int(inferred_month) <= 12:
                        current_month = inferred_month
                        logger.info(f"Inferred month from page number: {current_month}")
                        if current_month not in data:
                            data[current_month] = {}
                
                # If we still don't have a month, use a default
                if not current_month:
                    if page_num < 2:
                        current_month = "01"  # Default to January for early pages
                    else:
                        continue  # Skip if we can't determine the month
                
                # Process each line for prayer times
                for line in lines:
                    # Skip lines that don't contain prayer times
                    if not re.search(r'\d+:\d+', line):
                        continue
                    
                    # Log the line for debugging
                    logger.debug(f"Processing line: {line}")
                    
                    # Try multiple patterns to match different formats
                    
                    # Pattern 1: Standard format with all fields
                    pattern1 = r'(\d+)\s+([^\s]+)\s+(\d+)\s+(.*?)\s+(\d+:\d+)\s+(\d+:\d+)\s+(\d+:\d+)\s+(\d+:\d+)\s+(\d+:\d+)\s+(\d+:\d+)\s+(\d+:\d+)\s+(\d+:\d+)'
                    match1 = re.search(pattern1, line)
                    
                    # Pattern 2: Alternative format with fewer fields
                    pattern2 = r'(\d+)[^\d]+(\d+)[^\d]+(.*?)(\d{1,2}:\d{2})\s+(\d{1,2}:\d{2})\s+(\d{1,2}:\d{2})\s+(\d{1,2}:\d{2})\s+(\d{1,2}:\d{2})\s+(\d{1,2}:\d{2})\s+(\d{1,2}:\d{2})'
                    match2 = re.search(pattern2, line)
                    
                    # Pattern 3: Simpler pattern just looking for a day number followed by times
                    pattern3 = r'^\s*(\d+)(?:\D+(\d+))?(?:\D+([^\d]*))?(?:\D+(\d{1,2}:\d{2}))?(?:\D+(\d{1,2}:\d{2}))?(?:\D+(\d{1,2}:\d{2}))?(?:\D+(\d{1,2}:\d{2}))?(?:\D+(\d{1,2}:\d{2}))?(?:\D+(\d{1,2}:\d{2}))?(?:\D+(\d{1,2}:\d{2}))?(?:\D+(\d{1,2}:\d{2}))?'
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
            
            # If no data was extracted, try using the table extraction method
            if not data:
                logger.warning("No data extracted using text-based extraction. Trying table extraction.")
                data = extract_prayer_times_structured(pdf_path, year)
            
            # Ensure all months are represented in the data
            for month_num in range(1, 13):
                month_str = str(month_num).zfill(2)
                if month_str not in data:
                    data[month_str] = {}
            
            # Apply manual corrections for specific dates
            apply_manual_corrections(data, year)
    
    except Exception as e:
        logger.error(f"Error extracting data from PDF: {str(e)}")
        raise
    
    logger.info(f"Total days extracted: {sum(len(days) for days in data.values())}")
    return data

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
                                "festat_fetare_dhe_shenime_te_tjera_astronomike": fest,
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
                            logger.warning(f"Error processing row: {str(e)}")
            except Exception as e:
                logger.warning(f"Error processing table: {str(e)}")
    except Exception as e:
        logger.error(f"Error extracting data from PDF: {str(e)}")
    return data 