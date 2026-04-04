# SRE Incident Response Environment — Docker Image
# Runs FastAPI server on port 7860 (HuggingFace Spaces standard)

FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# HF Spaces standard port
EXPOSE 7860

# Run FastAPI server from root — imports resolve correctly
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
