# Container image for the InsurClaim AI application.
FROM python:3.13-slim

# Keep Python output unbuffered and skip .pyc files - nicer for containers.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first so this layer is cached when only code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code.
COPY insurclaim ./insurclaim

# Default command just prints the CLI help; docker-compose overrides it.
CMD ["python", "-m", "insurclaim.main", "--help"]
