FROM python:3.9-slim

# Copying requirements separately prevents re-running pip install on every code change.
COPY requirements.txt ./

# Install production dependencies.
RUN pip install -r requirements.txt

# Copy local code to the container image.
COPY app /app

# Allow statements and log messages to immediately appear in the logs
ENV PYTHONUNBUFFERED True

# Secrets injected into container environment variables from host
ENV STRAVA_CLIENT_ID replace
ENV STRAVA_CLIENT_SECRET replace
ENV STRAVA_REFRESH_TOKEN replace
ENV ACCUWEATHER_API_KEY replace

# Run the service on container startup from /app directory
WORKDIR /app
CMD exec hypercorn -b 0.0.0.0:80 --access-logfile - main:app
