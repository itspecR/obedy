FROM python:3.12.15

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt

COPY backend/ .

ARG APP_RELEASE=""
ENV APP_RELEASE=$APP_RELEASE

RUN useradd --system --no-create-home obedy
USER obedy

CMD ["gunicorn", "config.wsgi:application", "--bind", "127.0.0.1:8000", "--workers", "3", "--worker-class", "gthread", "--threads", "4", "--timeout", "120", "--access-logfile", "-"]
