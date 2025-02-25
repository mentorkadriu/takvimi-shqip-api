# How to Use This Project

### Place Your PDF Files:
Create a folder named takvimi-pdf in the root of your project (if it doesn’t already exist). Then put your PDF files there using the naming pattern (for example, takvimi2025.pdf).

### Build and Run the Container:
Open your terminal in the project directory and run:

```bash
docker-compose up --build
```

### Extracted Data via API Endpoints:

To see a list of available PDF files (and their filenames), visit:
```
http://localhost:5000/api/takvimi
```

To extract and retrieve data from a specific PDF file (for example, for 2025), visit:
```
http://localhost:5000/api/takvimi/2025.json
```

# takvimi-shqip-api
