import os
import requests
import re
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# Load environment variables
load_dotenv()

# GitHub API configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_API = "https://api.github.com"

app = Flask(__name__)
CORS(app)

def get_headers():
    """Generate headers with the stored token."""
    return {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

def check_issues_enabled(owner, repo):
    """Check if issues are enabled in the target repository."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}"
    headers = get_headers()
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return False
        
    repo_data = response.json()
    return repo_data.get('has_issues', False)

def parse_issue_url(url):
    """Parse GitHub issue URL to extract owner, repo, and issue number."""
    pattern = r'https://github\.com/([^/]+)/([^/]+)/issues/(\d+)'
    match = re.match(pattern, url)
    if not match:
        raise ValueError("Invalid GitHub issue URL format")
    return match.groups()

def parse_fork_url(url):
    """Parse GitHub repository URL to extract owner and repo."""
    pattern = r'https://github\.com/([^/]+)/([^/]+)/?'
    match = re.match(pattern, url)
    if not match:
        raise ValueError("Invalid GitHub repository URL format")
    return match.groups()

def get_source_issue(owner, repo, issue_number):
    """Fetch specific issue from source repository."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}"
    headers = get_headers()
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None
    
    return response.json()

def create_target_issue(target_owner, target_repo, issue_data):
    """Create issue in target repository."""
    url = f"{GITHUB_API}/repos/{target_owner}/{target_repo}/issues"
    headers = get_headers()
    
    # Prepare the issue data
    new_issue = {
        'title': issue_data['title'],
        'body': f"{issue_data['body']}\n\n---\n*Cloned from original issue: {issue_data['html_url']}*",
        'labels': [label['name'] for label in issue_data.get('labels', [])],
    }
    
    response = requests.post(url, headers=headers, json=new_issue)
    if response.status_code != 201:
        return None
    
    return response.json()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/clone-issue', methods=['POST'])
def clone_issue():
    data = request.json
    issue_url = data.get('issue_url')
    target_fork_url = data.get('target_fork_url')
    
    if not GITHUB_TOKEN:
        return jsonify({'error': 'GitHub token not set in .env file'}), 400
    
    if not issue_url or not target_fork_url:
        return jsonify({'error': 'Missing issue URL or target fork URL'}), 400
    
    try:
        # Parse the issue URL to get components
        source_owner, source_repo, issue_number = parse_issue_url(issue_url)
        
        # Parse the target fork URL
        target_owner, target_repo = parse_fork_url(target_fork_url)
        
        # Check if issues are enabled in target repository
        if not check_issues_enabled(target_owner, target_repo):
            return jsonify({'error': 'Issues are disabled in the target repository'}), 400
        
        # Get the source issue
        issue = get_source_issue(source_owner, source_repo, issue_number)
        
        if not issue:
            return jsonify({'error': 'Failed to fetch the source issue'}), 400
        
        # Create the issue in target repository
        new_issue = create_target_issue(target_owner, target_repo, issue)
        
        if not new_issue:
            return jsonify({'error': 'Failed to create issue in target repository'}), 400
        
        return jsonify({
            'message': 'Issue successfully cloned!',
            'new_issue_url': new_issue['html_url']
        }), 200
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    app.run(debug=True)
