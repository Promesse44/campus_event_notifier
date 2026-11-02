FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /app app \
    && mkdir -p /data \
    && chown app:app /data

COPY --chown=app:app event_notifier ./event_notifier

USER app
EXPOSE 8000
VOLUME ["/data"]

CMD ["python", "-m", "event_notifier", "--host", "0.0.0.0", "--port", "8000", "--data-file", "/data/events.json"]
