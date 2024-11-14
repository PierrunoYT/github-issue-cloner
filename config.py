"""Configuration settings for the GitHub Issue Cloner."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# GitHub API configuration
GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# Request configuration
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))  # seconds
RATE_LIMIT_WARNING = int(os.getenv('RATE_LIMIT_WARNING', '10'))  # Warn when remaining requests are below this number

# Content limits
MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '1048576'))  # 1MB max request size
MAX_ISSUE_TITLE_LENGTH = int(os.getenv('MAX_ISSUE_TITLE_LENGTH', '256'))
MAX_ISSUE_BODY_LENGTH = int(os.getenv('MAX_ISSUE_BODY_LENGTH', '65536'))  # 64KB

# Security settings
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')
ENABLE_RATE_LIMITING = os.getenv('ENABLE_RATE_LIMITING', 'true').lower() == 'true'

# HTTP Status Codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_NOT_FOUND = 404
HTTP_FORBIDDEN = 403
HTTP_CONFLICT = 409
HTTP_TOO_MANY_REQUESTS = 429

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'app.log')
MAX_LOG_SIZE = int(os.getenv('MAX_LOG_SIZE', '10485760'))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
