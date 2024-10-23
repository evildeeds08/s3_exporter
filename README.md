[English Version](./README.md) | [Русская версия](./README.ru.md)

# S3 Prometheus Exporter

This project is a Prometheus exporter that collects and exposes metrics from an S3 bucket (using Rclone). The exporter is designed to run in a Docker container, with HTTPS and Basic Auth for security. Metrics are periodically updated and made available for Prometheus to scrape.

## Features
- Collects metrics from an S3 bucket, including file names and their last modified timestamps.
- Supports HTTPS with SSL certificates.
- Uses Basic Authentication for secure access.
- Configurable update interval and other settings via environment variables.

## Prerequisites

- Docker
- Docker Compose
- Prometheus (for scraping metrics)
- Rclone configured for S3 access (with the `rclone.conf` file)

## Setup and Usage

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/s3-prometheus-exporter.git
cd s3-prometheus-exporter
```
### 2. Configure environment variables

```bash
mv .env.example .env
```


Edit the .env file to set up your S3 bucket name, Rclone configuration, and other required settings:

```bash
# Name of your S3 bucket
BUCKET_NAME=your-s3-bucket-name

# Name of the Rclone configuration
RCLONE_REMOTE=your-rclone-config

# Interval for updating metrics (in seconds)
INTERVAL=60

# Port for the HTTPS server
PORT=9337

# Basic Auth credentials
BASIC_AUTH_USER=your-user
BASIC_AUTH_PASS=your-password

# SSL certificate and key files for HTTPS
SSL_CERT_FILE=/app/certs/server.crt
SSL_KEY_FILE=/app/certs/server.key
```

### 3. Add Rclone configuration
Ensure your rclone.conf file is correctly set up for your S3 provider.

### 4. Generating SSL Certificates or Using Your Own

This project requires SSL certificates to secure the connection. You can either generate self-signed certificates for development or provide your own certificates if you have them from a certificate authority (CA).

#### 4.1. Generate Self-Signed SSL Certificates (for development)

If you don't have your own SSL certificates, you can generate self-signed certificates for testing purposes using the following command:

```bash
mkdir -p certs
openssl req -x509 -newkey rsa:4096 -keyout certs/server.key -out certs/server.crt -days 365 -nodes -subj "/CN=localhost"
```
#### 4.2 Use Your Own SSL Certificates
If you already have valid SSL certificates from a certificate authority (CA), you can simply place the certificate and key files in the certs/ directory. Update the paths in the .env file accordingly:
```
SSL_CERT_FILE=/app/certs/your-certificate.crt
SSL_KEY_FILE=/app/certs/your-private.key
```
Now, the exporter will use your SSL certificate for HTTPS communication.

### 5. Build and run the Docker container
Use Docker Compose to build and run the container:

```bash
docker-compose up --build
```

### 6. Access the metrics
Once the container is running, you can access the Prometheus metrics via HTTPS on the port you defined (default: 9337):

```bash
https://your-server-ip:9337/metrics
```
You will need to provide the Basic Auth credentials that you set in the .env file.

### 7. Adding to Prometheus
To scrape the exporter, add the following job configuration to your Prometheus prometheus.yml:

```bash
scrape_configs:
  - job_name: 's3_exporter'
    basic_auth:
      username: 'your-user'
      password: 'your-password'
    static_configs:
      - targets: ['your-server-ip:9337']
```

