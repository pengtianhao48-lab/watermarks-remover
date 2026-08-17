FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN apt-get update \
    && apt-get install -y --no-install-recommends libimage-exiftool-perl qpdf \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt \
    && python -m spacy download en_core_web_sm \
    && python -c "import nltk; nltk.download('wordnet'); nltk.download('omw-1.4')"

COPY . .

CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
