"""Flask web application for cloning GitHub issues."""
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import logging
from config import GITHUB_TOKEN, MAX_CONTENT_LENGTH
from github_utils import (
    validate_token, parse_issue_url, parse_fork_url,
    check_issues_enabled, get_source_issue, create_target_issue,
    issue_exists, GitHubError
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import bleach

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per day", "10 per minute"]
)

def validate_request_data(data):
    """
    Validate the incoming request data.
    
    Args:
        data: JSON request data
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not isinstance(data, dict):
        return False, "Invalid request format"
    
    issue_url = data.get('issue_url', '').strip()
    target_fork_url = data.get('target_fork_url', '').strip()
    
    if not issue_url:
        return False, "Issue URL is required"
    if not target_fork_url:
        return False, "Target fork URL is required"
        
    # Sanitize URLs
    issue_url = bleach.clean(issue_url)
    target_fork_url = bleach.clean(target_fork_url)
    
    # Basic URL format validation
    if not issue_url.startswith('https://github.com/'):
        return False, "Invalid issue URL format"
    if not target_fork_url.startswith('https://github.com/'):
        return False, "Invalid target fork URL format"
    
    return True, None

@app.route('/')
def index() -> str:
    """Render the main page."""
    return render_template('index.html')

@app.route('/clone-issue', methods=['POST'])
@limiter.limit("10 per minute")
def clone_issue():
    """
    Clone a GitHub issue to a target repository.
    
    Expected JSON payload:
    {
        "issue_url": "https://github.com/owner/repo/issues/number",
        "target_fork_url": "https://github.com/target_owner/target_repo"
    }
    
    Returns:
        JSON response with success message and new issue URL or error message
    """
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        is_valid, error_message = validate_request_data(data)
        if not is_valid:
            logger.error(f"Validation error: {error_message}")
            return jsonify({'error': error_message}), 400
        
        if not GITHUB_TOKEN:
            logger.error("GitHub token not set in .env file")
            return jsonify({'error': 'GitHub token not configured'}), 500
        
        if not validate_token(GITHUB_TOKEN):
            logger.error("Invalid GitHub token")
            return jsonify({'error': 'Invalid GitHub token'}), 401
        
        issue_url = bleach.clean(data['issue_url'])
        target_fork_url = bleach.clean(data['target_fork_url'])
        
        # Parse URLs to get components
        try:
            source_owner, source_repo, issue_number = parse_issue_url(issue_url)
            target_owner, target_repo = parse_fork_url(target_fork_url)
        except ValueError as e:
            logger.error(f"URL parsing error: {e}")
            return jsonify({'error': str(e)}), 400
        
        # Check if issues are enabled in target repository
        if not check_issues_enabled(GITHUB_TOKEN, target_owner, target_repo):
            logger.error(f"Issues are disabled in {target_owner}/{target_repo}")
            return jsonify({'error': 'Issues are disabled in the target repository'}), 400
        
        # Get the source issue
        issue = get_source_issue(GITHUB_TOKEN, source_owner, source_repo, issue_number)
        
        # Check for duplicate issues
        if issue_exists(GITHUB_TOKEN, target_owner, target_repo, issue['title']):
            logger.warning(f"Duplicate issue detected in {target_owner}/{target_repo}")
            return jsonify({'error': 'An issue with this title already exists in the target repository'}), 409
        
        # Create the issue in target repository
        new_issue = create_target_issue(GITHUB_TOKEN, target_owner, target_repo, issue)
        
        logger.info(f"Successfully cloned issue to {target_owner}/{target_repo}")
        return jsonify({
            'message': 'Issue successfully cloned!',
            'new_issue_url': new_issue['html_url']
        }), 200
    
    except GitHubError as e:
        logger.error(f"GitHub API error: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred. Please try again later.'}), 500

if __name__ == '__main__':
    app.run(debug=False)  # Set debug=False for production
