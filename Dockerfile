# Use a lightweight Python base
FROM python:3.13-slim

# Set the working directory to where your code lives
WORKDIR /app

# Install dependencies first (for caching layers)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
# This copies everything from your local 'app' folder into the container's '/app'
COPY app/ .

# Expose the Streamlit port
EXPOSE 8501

# Run the app
ENTRYPOINT ["streamlit", "run", "Dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]