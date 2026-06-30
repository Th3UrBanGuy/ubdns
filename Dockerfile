FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use the OS resolver instead of eventlet's greendns: greendns can be slow or
# fail outright on restrictive networks, stalling upstream DoH lookups.
ENV EVENTLET_NO_GREENDNS=yes

EXPOSE 8080

CMD ["gunicorn", "-k", "eventlet", "-b", "0.0.0.0:8080", "app:app"]
