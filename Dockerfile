FROM python:3.10-slim

WORKDIR /app

# Copy dependency list and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app folder including the "takvimi-pdf" folder
COPY . /app

EXPOSE 3010
CMD ["python", "app.py"]
