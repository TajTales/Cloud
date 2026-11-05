# Meikipop OCR Server Dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project definition and install dependencies
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install the package and dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Expose port
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the server (defaults to glensv2 provider on port 8080)
ENTRYPOINT ["meikipop-ocr-server"]
CMD ["--host", "0.0.0.0", "--port", "8080", "--provider", "glensv2"]

