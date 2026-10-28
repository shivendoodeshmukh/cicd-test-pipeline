FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create non-root user for security best practices
RUN useradd --create-home --uid 10001 demo

# Install dependencies first for optimal Docker layer caching
COPY requirements.txt pyproject.toml README.md ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and install application
COPY src/ ./src/
RUN pip install --no-cache-dir --no-deps .

USER demo

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

CMD ["uvicorn", "cicd_demo.server:app", "--host", "0.0.0.0", "--port", "80"]
