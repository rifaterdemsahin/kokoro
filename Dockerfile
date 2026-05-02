FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y espeak-ng espeak-ng-data libsndfile1 git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY index.html .
COPY main.py .

ENV PORT=8080
CMD ["python", "main.py"]
