# FROM python:3-alpine AS builder
 
# WORKDIR /app
 
# RUN python3 -m venv venv
# ENV VIRTUAL_ENV=/app/venv
# ENV PATH="$VIRTUAL_ENV/bin:$PATH"
 
# COPY requirements.txt .
# RUN pip install -r requirements.txt
 
# # Stage 2
# FROM python:3-alpine AS runner
 
# WORKDIR /app
 
# COPY --from=builder /app/venv venv
# COPY example_django example_django
 
# ENV VIRTUAL_ENV=/app/venv
# ENV PATH="$VIRTUAL_ENV/bin:$PATH"
# ENV PORT=8000
 
# EXPOSE ${PORT}
 
# CMD gunicorn --bind :${PORT} --workers 2 example_django.wsgi
# Stage 1: Builder
FROM python:3-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev

RUN python3 -m venv venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy and install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Optionally remove build dependencies to reduce image size
RUN apk del gcc musl-dev libffi-dev

# Stage 2: Runner
FROM python:3-alpine AS runner

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/venv venv
COPY example_django example_django

ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PORT=8000

EXPOSE ${PORT}

# Dynamically set the number of workers based on available CPU cores
CMD gunicorn --bind :${PORT} --workers $(($(nproc) * 2 + 1)) example_django.wsgi
