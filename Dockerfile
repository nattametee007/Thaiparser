FROM tiangolo/uvicorn-gunicorn-fastapi:python3.10

RUN apt-get update && apt-get install -y bzip2

WORKDIR /app

COPY main.py /app
COPY requirements.txt /app/requirements.txt
COPY thaiaddress /app/thaiaddress
COPY thaiaddress/data/sample_100_new.csv /app/thaiaddress/data/sample_100_new.csv

RUN pip install --no-cache-dir -r requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
