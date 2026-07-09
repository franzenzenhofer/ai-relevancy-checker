FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements-web.txt .
RUN pip install --no-cache-dir -r requirements-web.txt

# Copy application code
COPY core/ core/
COPY web/ web/
COPY run.py .
COPY run_web.py .

# Create data directories
RUN mkdir -p exports reports state/prompts results logs

# Non-root user for security
RUN useradd -m -s /bin/bash appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request; r=urllib.request.urlopen('http://localhost:8080/api/health', timeout=3); assert r.status==200"

CMD ["uvicorn", "web.server:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
