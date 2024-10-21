FROM python:3.11

RUN --mount=type=bind,source=requirements.txt,target=/root/requirements.txt pip install --no-cache-dir --upgrade -r /root/requirements.txt

WORKDIR /usr/local/product-microservice
COPY app app/

EXPOSE 8080
CMD ["fastapi", "run", "--port", "8080"]
