# Takvimi Shqip API - WORK IN PROGRESS

## Features

- Extract prayer times from Albanian Islamic Calendar PDFs for all 12 months
- Provide data in structured JSON format with prayer times, religious festivals, and astronomical notes
- Robust extraction with fallback mechanisms for different PDF formats
- Cache extracted data for improved performance
- Support for multiple years
- Extract specific PDF pages as CSV for data verification

## API Endpoints

- **GET /** - Home page with API information
- **GET /api/takvimi** - List available calendar years
- **GET /api/takvimi/{year}.json** - Get calendar data for a specific year
- **GET /api/takvimi/{year}/{month}.json** - Get calendar data for a specific month (01-12)
- **GET /api/takvimi/{year}/page/{page_num}.csv** - Extract a specific page from the PDF as CSV

## Data Structure

### Full Year Response

```json
{
  "year": "2025",
  "data": {
    "01": {
      "01": {
        "data_sipas_kal_boteror": 1,
        "dita_javes": "e mërkurë",
        "festat_fetare_dhe_shenime_te_tjera_astronomike": "Viti i Ri 2025, Hëna e re",
        "kohet": {
          "imsaku": "5:21",
          "sabahu": "5:41",
          "lindja_e_diellit": "7:13",
          "dreka": "11:48",
          "ikindia": "14:13",
          "akshami": "16:22",
          "jacia": "17:54",
          "gjatesia_e_dites": "9:09"
        }
      },
      "02": {
        // Data for January 2nd
      }
      // More days...
    },
    "02": {
      // Data for February
    }
    // More months...
  }
}
```

### Single Month Response

```json
{
  "year": "2025",
  "month": "01",
  "data": {
    "01": {
      "data_sipas_kal_boteror": 1,
      "dita_javes": "e mërkurë",
      "festat_fetare_dhe_shenime_te_tjera_astronomike": "Viti i Ri 2025, Hëna e re",
      "kohet": {
        "imsaku": "5:21",
        "sabahu": "5:41",
        "lindja_e_diellit": "7:13",
        "dreka": "11:48",
        "ikindia": "14:13",
        "akshami": "16:22",
        "jacia": "17:54",
        "gjatesia_e_dites": "9:09"
      }
    },
    "02": {
      // Data for January 2nd
    }
    // More days in this month...
  }
}
```

## PDF Extraction

The API extracts data from Albanian Islamic Calendar PDFs using a specialized extraction algorithm:

1. **Festival Information**: Extracts religious festivals and astronomical notes from the calendar
2. **Prayer Times**: Extracts prayer times for all days of each month
3. **Robust Extraction**: Uses multiple extraction methods with fallbacks if the primary method fails
4. **Comprehensive Coverage**: Extracts data for all 12 months of the year

The extraction process is optimized for the specific format of the Albanian Islamic Calendar, handling the unique layout and structure of these PDFs.

## Performance Optimizations

- **Reduced Logging**: Minimal logging for improved performance
- **Optimized Data Retrieval**: Multiple data access paths for faster responses
- **Smart Caching**: Efficiently uses cached data when available
- **Separate Month Files**: Smaller JSON payloads for faster loading
- **Fallback Mechanisms**: Tries multiple sources before extracting from PDF

## Caching Behavior

- **Month Data**: Caching is enabled by default for month-specific requests
- **Full Year Data**: Caching is disabled by default for full year requests
- **Override**: Add `?use_cache=true` or `?use_cache=false` to your request to override the default behavior

## Setup and Installation

### Using Docker

1. Clone the repository:
   ```
   git clone https://github.com/mentorkadriu/takvimi-shqip-api.git
   cd takvimi-shqip-api
   ```

2. Place your PDF files in the `takvimi-pdf` directory:
   ```
   mkdir -p takvimi-pdf
   cp /path/to/your/takvimi2025.pdf takvimi-pdf/
   ```

3. Build and run the Docker container:
   ```
   docker-compose build
   docker-compose up
   ```

4. The API will be available at http://localhost:3010

### Manual Installation

1. Clone the repository:
   ```
   git clone https://github.com/mentorkadriu/takvimi-shqip-api.git
   cd takvimi-shqip-api
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Place your PDF files in the `takvimi-pdf` directory:
   ```
   mkdir -p takvimi-pdf
   cp /path/to/your/takvimi2025.pdf takvimi-pdf/
   ```

4. Run the application:
   ```
   python app.py
   ```

5. The API will be available at http://localhost:3010

## Project Structure

```
takvimi-shqip-api/
├── app.py                  # Main application entry point
├── routes.py               # API routes and endpoints
├── config.py               # Configuration settings
├── requirements.txt        # Project dependencies
├── services/
│   ├── pdf_extraction.py   # PDF extraction functionality
│   └── data_manager.py     # Data caching and management
├── utils/                  # Utility functions
├── takvimi-pdf/            # Directory for PDF files
├── api/                    # Directory for cached JSON files
│   ├── 2025.json           # Full year data
│   └── 2025/               # Directory for monthly data
│       ├── 01.json         # January data
│       ├── 02.json         # February data
│       └── ...             # Other months
├── Dockerfile              # Docker configuration
└── docker-compose.yml      # Docker Compose configuration
```

## Error Handling

The API includes comprehensive error handling:

- **404**: PDF file or requested resource not found
- **400**: Invalid request parameters
- **500**: Server error processing the request
- **Fallback Mechanisms**: Multiple extraction methods to handle different PDF formats

## License

This project is open source and available under the MIT License.
