FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY application-backend/requirements.lock application-backend/requirements.lock
RUN pip install --no-cache-dir -r application-backend/requirements.lock
RUN pip install --no-cache-dir "PyJWT[crypto]"
COPY application-backend/src application-backend/src
COPY application-backend/schema application-backend/schema
COPY contracts contracts
COPY shared shared
COPY docs/CT-02-INTEGRATION-GUIDE.md docs/CT-02-INTEGRATION-GUIDE.md
RUN useradd --system --uid 10001 app && mkdir -p /tmp/appdata && chown app /tmp/appdata
USER app
ENV PYTHONPATH=/app/application-backend/src \
    APP_ENV=cloud DEPLOYMENT_MODE=cloud APP_HOST=0.0.0.0 APP_PORT=8081 \
    APP_DATA_DIR=/tmp/appdata PERSISTENCE_ENABLED=1 LOCAL_AUTH_ENABLED=1
EXPOSE 8081
CMD ["python", "-m", "lingualive_api"]