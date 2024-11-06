import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
import logging
from flask_cors import CORS
from github_utils import (
    validate_token, parse_issue_url, parse_fork_url,
    check_issues_enabled, get_source_issue, create_target_issue,
    GitHubError
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GitHub API configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clone-issue', methods=['POST'])
def clone_issue():
    data = request.json
    issue_url = data.get('issue_url')
    target_fork_url = data.get('target_fork_url')
    
    if not GITHUB_TOKEN:
        logger.error("GitHub token not set in .env file")
        return jsonify({'error': 'GitHub token not set in .env file'}), 400
    
    if not validate_token(GITHUB_TOKEN):
        logger.error("Invalid GitHub token")
        return jsonify({'error': 'Invalid GitHub token'}), 401
    
    if not issue_url or not target_fork_url:
        logger.error("Missing issue URL or target fork URL")
        return jsonify({'error': 'Missing issue URL or target fork URL'}), 400
    
    try:
        # Parse the issue URL to get components
        source_owner, source_repo, issue_number = parse_issue_url(issue_url)
        
        # Parse the target fork URL
        target_owner, target_repo = parse_fork_url(target_fork_url)
        
        # Check if issues are enabled in target repository
        if not check_issues_enabled(GITHUB_TOKEN, target_owner, target_repo):
            logger.error(f"Issues are disabled in {target_owner}/{target_repo}")
            return jsonify({'error': 'Issues are disabled in the target repository'}), 400
        
        # Get the source issue
        issue = get_source_issue(GITHUB_TOKEN, source_owner, source_repo, issue_number)
        
        # Create the issue in target repository
        new_issue = create_target_issue(GITHUB_TOKEN, target_owner, target_repo, issue)
        
        logger.info(f"Successfully cloned issue to {target_owner}/{target_repo}")
        return jsonify({
            'message': 'Issue successfully cloned!',
            'new_issue_url': new_issue['html_url']
        }), 200
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({'error': str(e)}), 400
    except GitHubError as e:
        logger.error(f"GitHub API error: {e}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)