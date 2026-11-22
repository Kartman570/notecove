FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY notecove notecove
RUN useradd --create-home notes && mkdir /data && chown notes:notes /data
USER notes
ENV NOTECOVE_DB=/data/notes.sqlite3
EXPOSE 8000
CMD ["uvicorn", "notecove.api:create_app", "--factory", "--host", "0.0.0.0"]
