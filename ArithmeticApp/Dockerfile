# Use a lightweight official Python image
FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Set working directory inside the container
WORKDIR /app

# Copy only requirements first (for efficient caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project files
COPY . .

# Expose Flask’s default port
EXPOSE 5000

# Run the app
CMD ["python", "app.py"]
