FROM python:3.12-alpine

WORKDIR /app
COPY server.py .
COPY index.html .

RUN adduser -D -u 1001 portal && chown -R portal:portal /app
USER portal

EXPOSE 8080

CMD ["python", "server.py"]
