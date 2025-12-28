FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY protoxol_triage.py .
COPY rules_sample.yar .

CMD ["sleep", "infinity"]


