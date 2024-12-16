"""GitHub utility functions for interacting with the GitHub API."""
import re
import requests
import logging
from datetime import datetime
from typing import Tuple, Dict, Optional, Any, List, Union
from config import (
    GITHUB_API, GITHUB_TOKEN, REQUEST_TIMEOUT,
    RATE_LIMIT_WARNING, HTTP_OK, HTTP_CREATED,
    HTTP_NOT_FOUND, HTTP_FORBIDDEN
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubError(Exception):
    """Custom exception for GitHub API errors."""
    pass

def validate_token(token: str) -> bool:
    """
    Validate GitHub token by making a test API call.
    
    Args:
        token: GitHub personal access token
        
    Returns:
        bool: True if token is valid, False otherwise
    """
    headers = get_headers(token)
    try:
        response = requests.get(
            f"{GITHUB_API}/user",
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        return response.status_code == HTTP_OK
    except requests.Timeout:
        logger.error("Timeout while validating GitHub token")
        return False
    except requests.RequestException as e:
        logger.error(f"Error validating GitHub token: {e}")
        return False

def get_headers(token: str) -> Dict[str, str]:
    """
    Generate headers with the provided token.
    
    Args:
        token: GitHub personal access token
        
    Returns:
        Dict containing the necessary headers for GitHub API requests
    """
    return {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

def check_issues_enabled(token: str, owner: str, repo: str) -> bool:
    """
    Check if issues are enabled in the target repository.
    
    Args:
        token: GitHub personal access token
        owner: Repository owner
        repo: Repository name
        
    Returns:
        bool: True if issues are enabled, False otherwise
        
    Raises:
        GitHubError: If there's an error checking the repository
    """
    url = f"{GITHUB_API}/repos/{owner}/{repo}"
    headers = get_headers(token)
    
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        _check_rate_limit(response)
        
        if response.status_code == HTTP_NOT_FOUND:
            raise GitHubError(f"Repository {owner}/{repo} not found")
        elif response.status_code != HTTP_OK:
            raise GitHubError(f"Failed to check repository: {response.status_code}")
            
        repo_data = response.json()
        return repo_data.get('has_issues', False)
    except requests.Timeout:
        logger.error(f"Timeout checking issues for {owner}/{repo}")
        raise GitHubError("Request timed out while checking repository")
    except requests.RequestException as e:
        raise GitHubError(f"Network error while checking repository: {str(e)}")

def parse_issue_url(url: str) -> Tuple[str, str, str]:
    """
    Parse GitHub issue URL to extract owner, repo, and issue number.
    
    Args:
        url: GitHub issue URL
        
    Returns:
        Tuple containing (owner, repo, issue_number)
        
    Raises:
        ValueError: If URL format is invalid
    """
    pattern = r'https://github\.com/([^/]+)/([^/]+)/issues/(\d+)'
    match = re.match(pattern, url)
    if not match:
        raise ValueError("Invalid GitHub issue URL format. Expected: https://github.com/owner/repo/issues/number")
    return match.groups()

def parse_fork_url(url: str) -> Tuple[str, str]:
    """
    Parse GitHub repository URL to extract owner and repo.
    
    Args:
        url: GitHub repository URL
        
    Returns:
        Tuple containing (owner, repo)
        
    Raises:
        ValueError: If URL format is invalid
    """
    pattern = r'https://github\.com/([^/]+)/([^/]+)/?'
    match = re.match(pattern, url)
    if not match:
        raise ValueError("Invalid GitHub repository URL format. Expected: https://github.com/owner/repo")
    return match.groups()

def get_source_issue(token: str, owner: str, repo: str, issue_number: str) -> Dict[str, Any]:
    """
    Fetch specific issue from source repository.
    
    Args:
        token: GitHub personal access token
        owner: Repository owner
        repo: Repository name
        issue_number: Issue number to fetch
        
    Returns:
        Dict containing the issue data
        
    Raises:
        GitHubError: If there's an error fetching the issue
    """
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}"
    headers = get_headers(token)
    
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        _check_rate_limit(response)
        
        if response.status_code == HTTP_NOT_FOUND:
            raise GitHubError(f"Issue #{issue_number} not found in {owner}/{repo}")
        elif response.status_code == HTTP_FORBIDDEN:
            raise GitHubError("Rate limit exceeded or insufficient permissions")
        elif response.status_code != HTTP_OK:
            raise GitHubError(f"Failed to fetch issue: {response.status_code}")
        
        return response.json()
    except requests.Timeout:
        logger.error(f"Timeout fetching issue #{issue_number} from {owner}/{repo}")
        raise GitHubError("Request timed out while fetching issue")
    except requests.RequestException as e:
        raise GitHubError(f"Network error while fetching issue: {str(e)}")

def create_target_issue(token: str, target_owner: str, target_repo: str, issue_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create issue in target repository.
    
    Args:
        token: GitHub personal access token
        target_owner: Target repository owner
        target_repo: Target repository name
        issue_data: Source issue data
        
    Returns:
        Dict containing the created issue data
        
    Raises:
        GitHubError: If there's an error creating the issue
    """
    url = f"{GITHUB_API}/repos/{target_owner}/{target_repo}/issues"
    headers = get_headers(token)
    
    new_issue = {
        'title': issue_data['title'],
        'body': f"{issue_data['body']}\n\n*Note: Images and attachments may not display correctly.*\n\n---\n*Cloned from original issue: {issue_data['html_url']}*",
        'labels': [label['name'] for label in issue_data.get('labels', [])],
        'state': issue_data.get('state', 'open')
    }
    
    try:
        response = requests.post(url, headers=headers, json=new_issue, timeout=REQUEST_TIMEOUT)
        _check_rate_limit(response)
        
        if response.status_code == HTTP_FORBIDDEN:
            raise GitHubError("Rate limit exceeded or insufficient permissions")
        elif response.status_code != HTTP_CREATED:
            raise GitHubError(f"Failed to create issue: {response.status_code}")
        
        return response.json()
    except requests.Timeout:
        logger.error(f"Timeout creating issue in {target_owner}/{target_repo}")
        raise GitHubError("Request timed out while creating issue")
    except requests.RequestException as e:
        raise GitHubError(f"Network error while creating issue: {str(e)}")

def issue_exists(token: str, owner: str, repo: str, title: str) -> bool:
    """
    Check if an issue with the given title exists in the repository.
    
    Args:
        token: GitHub personal access token
        owner: Repository owner
        repo: Repository name
        title: Issue title to check
    
    Returns:
        True if an issue with the title exists, False otherwise
    """
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues"
    headers = get_headers(token)
    params = {'state': 'all', 'per_page': 100}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        _check_rate_limit(response)
        
        if response.status_code != HTTP_OK:
            raise GitHubError(f"Failed to fetch issues: {response.status_code}")
        
        issues = response.json()
        return any(issue['title'] == title for issue in issues)
    except requests.Timeout:
        logger.error(f"Timeout while checking for existing issues in {owner}/{repo}")
        raise GitHubError("Request timed out while checking for existing issues")
    except requests.RequestException as e:
        raise GitHubError(f"Network error while checking for existing issues: {str(e)}")

def _check_rate_limit(response: requests.Response) -> None:
    """
    Check remaining rate limit and log warning if low.
    
    Args:
        response: Response object from GitHub API request
        
    Raises:
        GitHubError: If rate limit is exceeded
    """
    remaining = response.headers.get('X-RateLimit-Remaining')
    if remaining is not None:
        remaining = int(remaining)
        if remaining < RATE_LIMIT_WARNING:
            logger.warning(f"Only {remaining} GitHub API requests remaining")
        if remaining == 0:
            reset_timestamp = int(response.headers.get('X-RateLimit-Reset', 0))
            reset_time = datetime.fromtimestamp(reset_timestamp).strftime('%Y-%m-%d %H:%M:%S')
            raise GitHubError(f"GitHub API rate limit exceeded. Resets at: {reset_time}")
