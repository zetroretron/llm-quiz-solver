# Use the official Playwright image (Pre-installed browsers = FAST build)
# Version: 2.1.9 - Image diff + tools fix
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# "Download if needed, else use what is there"
# This command checks if browsers are installed. 
# Since we use the official image, it will see them and skip downloading (Fast).
# If something was missing, it would download it.
RUN playwright install

# Copy application code
COPY . .

# Fix permissions: Allow any user to write to the app directory
# This avoids the "User already exists" error and works for any UID Hugging Face uses.
RUN chmod -R 777 /app

# Expose the standard Hugging Face port
EXPOSE 7860

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
