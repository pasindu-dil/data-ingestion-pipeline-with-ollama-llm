FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .

RUN echo "precedence ::ffff:0:0/96  100" >> /etc/gai.conf

RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
