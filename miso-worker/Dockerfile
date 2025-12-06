FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# FORCE UPGRADE to guarantee Flash support
RUN pip install --upgrade google-generativeai
COPY app/ .
CMD ["python", "worker.py"]
