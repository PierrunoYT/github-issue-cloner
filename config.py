"""Configuration settings for the GitHub Issue Cloner."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# GitHub API configuration
GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# Request configuration
REQUEST_TIMEOUT = 10  # seconds
RATE_LIMIT_WARNING = 10  # Warn when remaining requests are below this number

# HTTP Status Codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_NOT_FOUND = 404
HTTP_FORBIDDEN = 403
