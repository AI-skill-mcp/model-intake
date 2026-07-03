FROM python:3.12-slim
WORKDIR /app
COPY docker/etl/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY etl/ ./etl/
ENV PYTHONPATH=/app
CMD ["python", "-m", "etl.run"]
