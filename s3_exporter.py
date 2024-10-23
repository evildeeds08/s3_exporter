import os
import subprocess
import re
import ssl
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from prometheus_client import Gauge, generate_latest
from base64 import b64decode
import time
from datetime import datetime

# Setting up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')

# Fetching environment variables
BUCKET_NAME = os.getenv('BUCKET_NAME')
RCLONE_REMOTE = os.getenv('RCLONE_REMOTE', 'selectel')  # Using Selectel configuration by default
INTERVAL = int(os.getenv('INTERVAL', 60))
PORT = int(os.getenv('PORT', 9337))
BASIC_AUTH_USER = os.getenv('BASIC_AUTH_USER')
BASIC_AUTH_PASS = os.getenv('BASIC_AUTH_PASS')
SSL_CERT_FILE = os.getenv('SSL_CERT_FILE')
SSL_KEY_FILE = os.getenv('SSL_KEY_FILE')

# Checking if critical environment variables are set
if not BUCKET_NAME:
    logging.error("BUCKET_NAME environment variable is not set")
    exit(1)
if not RCLONE_REMOTE:
    logging.error("RCLONE_REMOTE environment variable is not set")
    exit(1)

# Rclone command to get the list of files
RCLONE_COMMAND = f"rclone lsl {RCLONE_REMOTE}:{BUCKET_NAME}"

# Metrics for the files
gauge_file_list = Gauge('s3_file_list', 'List of files in S3 bucket', ['filename'])
gauge_file_last_modified = Gauge('s3_file_last_modified', 'Last modified timestamp of files in S3 bucket', ['filename'])

# Regular expression to parse the lines from the rclone lsl output
rclone_pattern = re.compile(r'\s*(\d+)\s+(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2})\.\d+\s+(.+)')

# Function to get the list of files via rclone with logging
def get_file_list():
    try:
        logging.debug(f"Executing command: {RCLONE_COMMAND}")
        result = subprocess.run(RCLONE_COMMAND, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Logging the output of the command
        logging.debug(f"Rclone stdout: {result.stdout}")
        logging.debug(f"Rclone stderr: {result.stderr}")

        if result.returncode != 0:
            logging.error(f"Error running rclone command: {result.stderr}")
            return None

        # If no output, return None
        if not result.stdout.strip():
            logging.warning("Rclone command returned no output.")
            return None

        file_list = result.stdout.strip().split('\n')

        for file_info in file_list:
            match = rclone_pattern.match(file_info)
            if match:
                size, date, time_of_day, file_name = match.groups()
                logging.debug(f"Matched file: {file_name}, Size: {size}, Date: {date}, Time: {time_of_day}")

                # Add file to the file list metric
                gauge_file_list.labels(file_name).set(1)

                # Parse date and time into a timestamp
                file_timestamp_str = f"{date} {time_of_day}"
                file_timestamp = datetime.strptime(file_timestamp_str, '%Y-%m-%d %H:%M:%S').timestamp()
                logging.debug(f"File {file_name} last modified at: {file_timestamp}")

                # Add last modified timestamp metric for the file
                gauge_file_last_modified.labels(file_name).set(file_timestamp)

            else:
                logging.warning(f"Skipping malformed line: {file_info}")

    except Exception as e:
        logging.error(f"Exception in get_file_list: {e}")

# HTTP handler with Basic Authentication
class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Basic Authentication
        auth_header = self.headers.get('Authorization')
        if not auth_header or not self.check_auth(auth_header):
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="S3 Exporter"')
            self.end_headers()
            return

        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
            self.end_headers()
            self.wfile.write(generate_latest())
        else:
            self.send_response(404)
            self.end_headers()

    def check_auth(self, auth_header):
        auth_type, credentials = auth_header.split(' ')
        if auth_type.lower() == 'basic':
            decoded_credentials = b64decode(credentials).decode('utf-8')
            user, password = decoded_credentials.split(':')
            return user == BASIC_AUTH_USER and password == BASIC_AUTH_PASS
        return False

# Function to update metrics with logging
def update_metrics():
    while True:
        logging.info("Updating metrics...")
        get_file_list()  # Simply updates the list of files every INTERVAL seconds
        time.sleep(INTERVAL)

if __name__ == '__main__':
    # Start the HTTP server with SSL
    httpd = HTTPServer(('0.0.0.0', PORT), AuthHandler)

    # Set up SSL
    httpd.socket = ssl.wrap_socket(httpd.socket, certfile=SSL_CERT_FILE, keyfile=SSL_KEY_FILE, server_side=True)

    logging.info(f"Prometheus exporter running on port {PORT} with HTTPS and Basic Auth")

    # Start metric updates in a background thread
    import threading
    metrics_thread = threading.Thread(target=update_metrics)
    metrics_thread.start()

    # Start the HTTPS server
    httpd.serve_forever()

