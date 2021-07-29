FROM python:3.9.6-slim

WORKDIR /app

copy requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
ENV DOCKER=True

run chown -R 100:100 /app

USER 100:100

ENTRYPOINT ["python", "src/app.py"]

CMD [ "clients.txt" ]
