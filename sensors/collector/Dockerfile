FROM python:3.11-slim

WORKDIR /collector

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
