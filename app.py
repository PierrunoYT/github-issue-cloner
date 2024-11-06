"""Flask web application for cloning GitHub issues."""
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import logging
from config import GITHUB_TOKEN
from github_utils import (
    validate_token, parse_issue_url, parse_fork_url,
    check_issues_enabled, get_source_issue, create_target_issue,
    GitHubError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

@app.route('/')
def index() -> str:
    """Render the main page."""
    return render_template('index.html')

@app.route('/clone-issue', methods=['POST'])
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
        if not GITHUB_TOKEN:
            logger.error("GitHub token not set in .env file")
            return jsonify({'error': 'GitHub token not set in .env file'}), 400
        
        if not validate_token(GITHUB_TOKEN):
            logger.error("Invalid GitHub token")
            return jsonify({'error': 'Invalid GitHub token'}), 401
        
        data = request.json
        issue_url = data.get('issue_url')
        target_fork_url = data.get('target_fork_url')
        
        if not issue_url or not target_fork_url:
            logger.error("Missing issue URL or target fork URL")
            return jsonify({'error': 'Missing issue URL or target fork URL'}), 400
        
        # Parse URLs to get components
        source_owner, source_repo, issue_number = parse_issue_url(issue_url)
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
