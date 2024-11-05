import os
import requests
import re
from dotenv import load_dotenv
import time
import webbrowser

# Load environment variables
load_dotenv()

# GitHub API configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_API = "https://api.github.com"

def get_headers(token):
    """Generate headers with the provided token."""
    return {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }

def check_issues_enabled(token, owner, repo):
    """Check if issues are enabled in the target repository."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}"
    headers = get_headers(token)
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error checking repository: {response.status_code}")
        return False
        
    repo_data = response.json()
    return repo_data.get('has_issues', False)

def enable_issues_prompt(owner, repo):
    """Prompt user to enable issues and open the repository settings."""
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

def parse_issue_url(url):
    """Parse GitHub issue URL to extract owner, repo, and issue number."""
    pattern = r'https://github\.com/([^/]+)/([^/]+)/issues/(\d+)'
    match = re.match(pattern, url)
    if not match:
        raise ValueError("Invalid GitHub issue URL format")
    return match.groups()

def get_source_issue(token, owner, repo, issue_number):
    """Fetch specific issue from source repository."""
    url = f"{GITHUB_API}/repos/{owner}/{repo}/issues/{issue_number}"
    headers = get_headers(token)
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching issue: {response.status_code}")
        print(response.json())
        return None
    
    return response.json()

def get_forked_repo_details(token, original_owner, original_repo):
    """Get the user's forked repository details."""
    headers = get_headers(token)
    
    # Get authenticated user's username
    user_response = requests.get(f"{GITHUB_API}/user", headers=headers)
    if user_response.status_code != 200:
        print("Error fetching user information")
        return None
    
    username = user_response.json()['login']
    
    # Check if the user has a fork of the original repository
    forks_url = f"{GITHUB_API}/repos/{original_owner}/{original_repo}/forks"
    forks_response = requests.get(forks_url, headers=headers)
    
    if forks_response.status_code != 200:
        print("Error fetching forks")
        return None
    
    forks = forks_response.json()
    
    # Find the user's fork
    user_fork = next((fork for fork in forks if fork['owner']['login'] == username), None)
    
    if user_fork:
        return user_fork['owner']['login'], user_fork['name']
    else:
        print(f"No fork found for {original_owner}/{original_repo} under your account.")
        fork_url = f"https://github.com/{original_owner}/{original_repo}/fork"
        print(f"Please fork the repository first: {fork_url}")
        input("Press Enter after forking the repository...")
        
        # Retry getting forked repo details
        return get_forked_repo_details(token, original_owner, original_repo)

def create_target_issue(token, target_owner, target_repo, issue_data):
    """Create issue in target repository."""
    url = f"{GITHUB_API}/repos/{target_owner}/{target_repo}/issues"
    headers = get_headers(token)
    
    # Prepare the issue data
    new_issue = {
        'title': issue_data['title'],
        'body': f"{issue_data['body']}\n\n---\n*Cloned from original issue: {issue_data['html_url']}*",
        'labels': [label['name'] for label in issue_data.get('labels', [])],
    }
    
    response = requests.post(url, headers=headers, json=new_issue)
    if response.status_code != 201:
        print(f"Error creating issue: {response.status_code}")
        print(response.json())
        return None
    
    return response.json()

def main():
    """Main function to clone a specific issue."""
    if not GITHUB_TOKEN:
        print("Error: GitHub token not found. Please set GITHUB_TOKEN in .env file")
        return

    # Get source issue URL from user
    issue_url = input("Please paste the GitHub issue URL you want to clone: ").strip()
    
    try:
        # Parse the URL to get components
        source_owner, source_repo, issue_number = parse_issue_url(issue_url)
        
        # Get forked repository details
        target_details = get_forked_repo_details(GITHUB_TOKEN, source_owner, source_repo)
        
        if not target_details:
            print("Could not find or create a fork of the repository.")
            return
        
        target_owner, target_repo = target_details
        
        print(f"\nFetching issue #{issue_number} from {source_owner}/{source_repo}...")
        
        # Check if issues are enabled in target repository
        if not check_issues_enabled(GITHUB_TOKEN, target_owner, target_repo):
            enable_issues_prompt(target_owner, target_repo)
            # Check again after user action
            if not check_issues_enabled(GITHUB_TOKEN, target_owner, target_repo):
                print("\nIssues are still disabled. Please enable issues and try again.")
                return
        
        # Get the source issue
        issue = get_source_issue(GITHUB_TOKEN, source_owner, source_repo, issue_number)
        if not issue:
            print("Failed to fetch the source issue.")
            return
            
        print(f"Cloning issue: {issue['title']}")
        
        # Create the issue in target repository
        new_issue = create_target_issue(GITHUB_TOKEN, target_owner, target_repo, issue)
        
        if new_issue:
            print(f"\nSuccessfully cloned issue!")
            print(f"New issue URL: {new_issue['html_url']}")
        else:
            print("\nFailed to clone the issue.")
            
    except ValueError as e:
        print(f"Error: {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    main()
