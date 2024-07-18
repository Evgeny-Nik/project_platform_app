FROM python:alpine3.19

WORKDIR /app

COPY ./requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

RUN pip3 install Flask[async]

COPY . .

CMD ["python3", "-m", "gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "--config", "gunicorn.conf.py", "wsgi:app"]
