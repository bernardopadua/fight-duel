FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /fduel-backend

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . /fduel-backend

RUN useradd -m -u 1000 fdueluser && chown -R fdueluser:fdueluser /fduel-backend
USER fdueluser

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "core.asgi:application"]