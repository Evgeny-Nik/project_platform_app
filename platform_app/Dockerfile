FROM python:alpine3.19

# Install curl and Helm using apk (Alpine Package Management)
RUN apk update && \
    apk add --no-cache curl bash openssl && \
    curl -fsSL -o /tmp/get_helm.sh https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 && \
    chmod +x /tmp/get_helm.sh && \
    /tmp/get_helm.sh && \
    apk del --purge curl bash openssl && \
    rm -rf /var/cache/apk/*

WORKDIR /app

COPY ./requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

RUN pip3 install Flask[async]

COPY . .

# Ensure the session directory exists
RUN mkdir -p /tmp/flask_session/ && chmod -R 777 /tmp/flask_session/

CMD ["gunicorn","-c", "gunicorn.conf.py", "wsgi:app"]

# ENTRYPOINT ["python3"]

# CMD ["app.py"]