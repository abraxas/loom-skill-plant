FROM python:3.13-slim AS loom

WORKDIR /app

COPY src-v1.9.0/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src-v1.9.0/backend/app/ ./app/
COPY src-v1.9.0/backend/etc/ ./etc/

# Harness only: bearer map + file-backed Agent Registry. Product routers unmodified.
COPY lab_harness.py sitecustomize.py /usr/local/lib/python3.13/site-packages/
COPY poc.py /lab/poc.py

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV LAB_REGISTRY_PATH=/tmp/loom-190-skill-plant-registry.json
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
