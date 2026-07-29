FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app
RUN groupadd --system app && useradd --system --gid app --create-home app
COPY --chown=app:app src ./src
COPY --chown=app:app examples ./examples
USER app

ENTRYPOINT ["python", "-m", "semantic_metrics", "--catalog", "examples/catalog.json"]
CMD ["validate"]

