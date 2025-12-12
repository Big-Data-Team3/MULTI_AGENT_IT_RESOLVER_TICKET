
# Base Image (Python 3.11, lightweight, Cloud Run compatible)

FROM python:3.11-slim


# OS Dependencies (Cloud Run requires these for SSL, fonts)

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*


# Working directory

WORKDIR /app


# Copy requirements first for better layer caching

COPY requirements.txt .


# Install requirements (no cache for smaller container)

RUN pip install --no-cache-dir -r requirements.txt


# Copy all application files

COPY . .


# Streamlit Config (disable CORS, enable Cloud Run)

ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
ENV STREAMLIT_SERVER_PORT=8080
ENV PORT=8080

# (Cloud Run will inject AZURE_* and other env vars)


# Expose port (Cloud Run requirement)

EXPOSE 8080


# Start Streamlit

CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
