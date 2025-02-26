#!/usr/bin/env python3
import os
import json
import sys
import requests
from datetime import datetime

def test_local_json_files():
    """Test the JSON files saved in the api/takvimi directory"""
    json_dir = "api/takvimi"
    if not os.path.exists(json_dir):
        print(f"Error: Directory {json_dir} does not exist")
        return False
    
    json_files = [f for f in os.listdir(json_dir) if f.endswith(".json")]
    if not json_files:
        print(f"No JSON files found in {json_dir}")
        return False
    
    print(f"Found {len(json_files)} JSON files to test")
    
    success = True
    for json_file in json_files:
        file_path = os.path.join(json_dir, json_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            year = data.get("year")
            calendar_data = data.get("data", {})
            
            # Check if all months are present
            months = calendar_data.keys()
            if len(months) != 12:
                print(f"Warning: {json_file} has {len(months)} months instead of 12")
            
            # Check if each month has days
            total_days = 0
            for month, days in calendar_data.items():
                days_count = len(days)
                total_days += days_count
                if days_count == 0:
                    print(f"Warning: Month {month} in {json_file} has no days")
                else:
                    print(f"Month {month} has {days_count} days")
                    
                    # Test a sample day from each month
                    if days:
                        sample_day = next(iter(days))
                        day_data = days[sample_day]
                        
                        # Check if the day data has all required fields
                        required_fields = ["data_sipas_kal_boteror", "dita_javes", "kohet"]
                        for field in required_fields:
                            if field not in day_data:
                                print(f"Warning: Day {sample_day} in month {month} is missing field '{field}'")
                                success = False
                        
                        # Check if prayer times are present
                        if "kohet" in day_data:
                            prayer_times = day_data["kohet"]
                            required_times = ["imsaku", "sabahu", "lindja_e_diellit", "dreka", "ikindia", "akshami", "jacia"]
                            for time_field in required_times:
                                if time_field not in prayer_times:
                                    print(f"Warning: Day {sample_day} in month {month} is missing prayer time '{time_field}'")
                                    success = False
            
            print(f"Total days in {json_file}: {total_days}")
            if total_days < 28:
                print(f"Warning: {json_file} has fewer than 28 days in total")
                success = False
                
        except Exception as e:
            print(f"Error testing {json_file}: {str(e)}")
            success = False
    
    return success

def test_api_endpoints(base_url="http://localhost:3010"):
    """Test the API endpoints"""
    try:
        # Test home endpoint
        response = requests.get(f"{base_url}/")
        if response.status_code != 200:
            print(f"Error: Home endpoint returned status code {response.status_code}")
            return False
        
        print("Home endpoint test passed")
        
        # Test list endpoint
        response = requests.get(f"{base_url}/api/takvimi")
        if response.status_code != 200:
            print(f"Error: List endpoint returned status code {response.status_code}")
            return False
        
        data = response.json()
        available_years = data.get("available_years", [])
        processed_years = data.get("processed_years", [])
        
        print(f"Available years: {available_years}")
        print(f"Processed years: {processed_years}")
        
        # Test year endpoint for each available year
        for year in available_years:
            response = requests.get(f"{base_url}/api/takvimi/{year}.json")
            if response.status_code != 200:
                print(f"Error: Year endpoint for {year} returned status code {response.status_code}")
                continue
            
            data = response.json()
            calendar_data = data.get("data", {})
            
            # Check if all months are present
            months = calendar_data.keys()
            if len(months) != 12:
                print(f"Warning: API response for {year} has {len(months)} months instead of 12")
            
            # Check total days
            total_days = sum(len(days) for days in calendar_data.values())
            print(f"Total days in API response for {year}: {total_days}")
            if total_days < 28:
                print(f"Warning: API response for {year} has fewer than 28 days in total")
                return False
            
            # Check if each month has days
            for month, days in calendar_data.items():
                days_count = len(days)
                if days_count == 0:
                    print(f"Warning: Month {month} in API response for {year} has no days")
                else:
                    print(f"Month {month} has {days_count} days in API response for {year}")
                    
                    # Test a sample day from each month
                    if days:
                        sample_day = next(iter(days))
                        day_data = days[sample_day]
                        
                        # Check if the day data has all required fields
                        required_fields = ["data_sipas_kal_boteror", "dita_javes", "kohet"]
                        for field in required_fields:
                            if field not in day_data:
                                print(f"Warning: Day {sample_day} in month {month} in API response for {year} is missing field '{field}'")
                                return False
                        
                        # Check if prayer times are present
                        if "kohet" in day_data:
                            prayer_times = day_data["kohet"]
                            required_times = ["imsaku", "sabahu", "lindja_e_diellit", "dreka", "ikindia", "akshami", "jacia"]
                            for time_field in required_times:
                                if time_field not in prayer_times:
                                    print(f"Warning: Day {sample_day} in month {month} in API response for {year} is missing prayer time '{time_field}'")
                                    return False
            
            print(f"Total days in API response for {year}: {total_days}")
            if total_days < 28:
                print(f"Warning: API response for {year} has fewer than 28 days in total")
                return False
            
        return True
    except Exception as e:
        print(f"Error testing API endpoints: {str(e)}")
        return False 