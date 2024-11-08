"""Command line interface for cloning GitHub issues."""
import webbrowser
import requests
import logging
from typing import Tuple
from config import GITHUB_API, GITHUB_TOKEN, REQUEST_TIMEOUT
from github_utils import (
    validate_token, parse_issue_url, check_issues_enabled,
    get_source_issue, create_target_issue, get_headers,
    GitHubError, issue_exists
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def enable_issues_prompt(owner: str, repo: str) -> None:
    """
    Prompt user to enable issues and open the repository settings.
    
    Args:
        owner: Repository owner
        repo: Repository name
    """
    print("\nIssues are currently disabled in your repository.")
    print("To enable issues:")
    print("1. Go to your repository settings (opening in browser)")
    print("2. Scroll down to 'Features' section")
    print("3. Check the 'Issues' checkbox")
    print("4. Click 'Save' at the bottom of the page")
    
    settings_url = f"https://github.com/{owner}/{repo}/settings"
    
    input("\nPress Enter to open repository settings in your browser...")
    webbrowser.open(settings_url)
    
    input("\nAfter enabling issues, press Enter to continue...")

def get_forked_repo_details(token: str, original_owner: str, original_repo: str) -> Tuple[str, str]:
    """
    Get the user's forked repository details.
    
    Args:
        token: GitHub personal access token
        original_owner: Original repository owner
        original_repo: Original repository name
        
    Returns:
        Tuple containing (fork_owner, fork_repo)
        
    Raises:
        GitHubError: If there's an error getting fork details
    """
    headers = get_headers(token)
    
    try:
        # Get authenticated user's username
        user_response = requests.get(
            f"{GITHUB_API}/user",
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        if user_response.status_code != 200:
            raise GitHubError("Error fetching user information")
        username = user_response.json()['login']
        
        while True:
            # Check if the user has a fork of the original repository
            repo_response = requests.get(
                f"{GITHUB_API}/repos/{username}/{original_repo}",
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )
            
            if repo_response.status_code == 200:
                # Fork exists
                return username, original_repo
            elif repo_response.status_code == 404:
                # No fork found, prompt user to create one
                logger.info(f"No fork found for {original_owner}/{original_repo} under your account.")
                fork_url = f"https://github.com/{original_owner}/{original_repo}/fork"
                logger.info(f"Please fork the repository first: {fork_url}")
                input("Press Enter after forking the repository...")
            else:
                raise GitHubError("Error checking for forked repository")
                
    except requests.Timeout:
        raise GitHubError("Request timed out while getting fork details")
    except requests.RequestException as e:
        raise GitHubError(f"Network error while getting fork details: {str(e)}")

def main() -> None:
    """Main function to clone a specific issue."""
    try:
        if not GITHUB_TOKEN:
            raise GitHubError("GitHub token not found. Please set GITHUB_TOKEN in .env file")

        if not validate_token(GITHUB_TOKEN):
            raise GitHubError("Invalid GitHub token")

        # Get source issue URL from user
        issue_url = input("Please paste the GitHub issue URL you want to clone: ").strip()
        if not issue_url:
            raise ValueError("Issue URL cannot be empty")
            
        # Parse the URL to get components
        try:
            source_owner, source_repo, issue_number = parse_issue_url(issue_url)
        except ValueError as e:
            raise GitHubError(f"Invalid issue URL: {str(e)}")
        
        # Get forked repository details
        logger.info("Checking fork repository details...")
        target_owner, target_repo = get_forked_repo_details(GITHUB_TOKEN, source_owner, source_repo)
        
        logger.info(f"Fetching issue #{issue_number} from {source_owner}/{source_repo}...")
        
        # Check if issues are enabled in target repository
        if not check_issues_enabled(GITHUB_TOKEN, target_owner, target_repo):
            enable_issues_prompt(target_owner, target_repo)
            # Check again after user action
            if not check_issues_enabled(GITHUB_TOKEN, target_owner, target_repo):
                raise GitHubError("Issues are still disabled. Please enable issues and try again.")
        
        # Get the source issue
        issue = get_source_issue(GITHUB_TOKEN, source_owner, source_repo, issue_number)
        logger.info(f"Cloning issue: {issue['title']}")

        # Check if the issue is locked
        if issue.get('locked', False):
            logger.warning("The source issue is locked. Comments and interactions are limited.")

        # Check if the issue is closed
        if issue.get('state', '') == 'closed':
            logger.info("The source issue is closed. Cloning it as a closed issue.")

        # Check if the issue already exists in target repository
        logger.info("Checking if the issue already exists in the target repository...")
        if issue_exists(GITHUB_TOKEN, target_owner, target_repo, issue['title']):
            logger.error("An issue with the same title already exists in the target repository.")
            return

        # Create the issue in target repository
        new_issue = create_target_issue(GITHUB_TOKEN, target_owner, target_repo, issue)
        logger.info("Successfully cloned issue!")
        logger.info(f"New issue URL: {new_issue['html_url']}")
            
    except GitHubError as e:
        logger.error(f"GitHub error: {str(e)}")
    except ValueError as e:
        logger.error(f"Value error: {str(e)}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()
