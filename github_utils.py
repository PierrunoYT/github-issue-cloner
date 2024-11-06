import os
import re
import requests
import logging
from typing import Tuple, Dict, Optional, Any

GITHUB_API = "https://api.github.com"

class GitHubError(Exception):
    """Custom exception for GitHub API errors"""
    pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_token(token: str) -> bool:
    """Validate GitHub token by making a test API call"""
    headers = get_headers(token)
    try:
        response = requests.get(f"{GITHUB_API}/user", headers=headers, timeout=10)
        return response.status_code == 200
    except requests.Timeout:
        logger.error("Timeout while validating GitHub token")
        return False
    except requests.RequestException as e:
        logger.error(f"Error validating GitHub token: {e}")
        return False

def get_headers(token: str) -> Dict[str, str]:
    """Generate headers with the provided token."""
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json'
    }


def check_issues_enabled(token: str, owner: str, repo: str) -> bool:
    """Check if issues are enabled in the target repository."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}"
    headers = get_headers(token)
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.Timeout:
        logger.error(f"Timeout checking issues for {owner}/{repo}")
        raise GitHubError("Request timed out while checking repository")
    except requests.RequestException as e:
        raise GitHubError(f"Network error while checking repository: {str(e)}")
    
    if response.status_code == 404:
        raise GitHubError(f"Repository {owner}/{repo} not found")
    elif response.status_code != 200:
        raise GitHubError(f"Failed to check repository: {response.status_code}")
        
    repo_data = response.json()
    return repo_data.get('has_issues', False)

def parse_issue_url(url: str) -> Tuple[str, str, str]:
    """Parse GitHub issue URL to extract owner, repo, and issue number."""
    pattern = r'https://github\.com/([^/]+)/([^/]+)/issues/(\d+)'
    match = re.match(pattern, url)
    if not match:
        raise ValueError("Invalid GitHub issue URL format. Expected: https://github.com/owner/repo/issues/number")
    return match.groups()

def parse_fork_url(url: str) -> Tuple[str, str]:
    """Parse GitHub repository URL to extract owner and repo."""
    pattern = r'https://github\.com/([^/]+)/([^/]+)/?'
    match = re.match(pattern, url)
    if not match:
        raise ValueError("Invalid GitHub repository URL format. Expected: https://github.com/owner/repo")
    return match.groups()

def get_source_issue(token: str, owner: str, repo: str, issue_number: str) -> Optional[Dict[str, Any]]:
    """Fetch specific issue from source repository."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}"
    headers = get_headers(token)
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.Timeout:
        logger.error(f"Timeout fetching issue #{issue_number} from {owner}/{repo}")
        raise GitHubError("Request timed out while fetching issue")
    except requests.RequestException as e:
        raise GitHubError(f"Network error while fetching issue: {str(e)}")
    
    if response.status_code == 404:
        raise GitHubError(f"Issue #{issue_number} not found in {owner}/{repo}")
    elif response.status_code == 403:
        raise GitHubError("Rate limit exceeded or insufficient permissions")
    elif response.status_code != 200:
        raise GitHubError(f"Failed to fetch issue: {response.status_code}")

    # Check rate limits
    remaining = response.headers.get('X-RateLimit-Remaining')
    if remaining and int(remaining) < 10:
        logger.warning(f"Only {remaining} GitHub API requests remaining")
    
    return response.json()

def create_target_issue(token: str, target_owner: str, target_repo: str, issue_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create issue in target repository."""
    url = f"{GITHUB_API}/repos/{target_owner}/{target_repo}/issues"
    headers = get_headers(token)
    
    new_issue = {
        'title': issue_data['title'],
        'body': f"{issue_data['body']}\n\n---\n*Cloned from original issue: {issue_data['html_url']}*",
        'labels': [label['name'] for label in issue_data.get('labels', [])],
    }
    
    try:
        response = requests.post(url, headers=headers, json=new_issue, timeout=10)
    except requests.Timeout:
        logger.error(f"Timeout creating issue in {target_owner}/{target_repo}")
        raise GitHubError("Request timed out while creating issue")
    except requests.RequestException as e:
        raise GitHubError(f"Network error while creating issue: {str(e)}")
    
    if response.status_code == 403:
        raise GitHubError("Rate limit exceeded or insufficient permissions")
    elif response.status_code != 201:
        raise GitHubError(f"Failed to create issue: {response.status_code}")
    
    return response.json()
