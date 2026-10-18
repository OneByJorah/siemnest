FROM python:3.12-alpine

WORKDIR /app
COPY server.py .

RUN adduser -D -u 1001 analyst && chown -R analyst:analyst /app
USER analyst

EXPOSE 8090

CMD ["python", "server.py"]
