# Use official Python 3.11 image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and source code
COPY monitoring_service.py /app/

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn aiohttp python-dotenv

# Expose port
EXPOSE 8000

# Set environment variables (can also override at runtime)
ENV JAEGER_API=http://localhost:16686/api/traces

# Run FastAPI using Uvicorn
CMD ["uvicorn", "monitoring_service:app", "--host", "0.0.0.0", "--port", "8000"]
