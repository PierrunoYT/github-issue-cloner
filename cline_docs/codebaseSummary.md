## GitHub Issue Cloner - Codebase Overview

### Key Components
- `issue_cloner.py`: Main script handling issue cloning
- `.env.example`: Environment configuration template
- `requirements.txt`: Project dependencies

### Core Workflow
1. GitHub token authentication
2. Source issue URL parsing
3. Fork detection
4. Issue retrieval
5. Issue creation in forked repository

### Main Functions
- `get_forked_repo_details()`: Detect or guide fork creation
- `get_source_issue()`: Retrieve source issue details
- `create_target_issue()`: Clone issue to target repository
- `check_issues_enabled()`: Verify repository issue status

### Key Design Principles
- User-guided interaction
- Minimal configuration required
- Automatic error handling
- Transparent process

### Code Structure
- Modular function design
- Clear separation of concerns
- Comprehensive error handling
- Interactive user guidance

### Performance Considerations
- Efficient API call management
- Minimal external dependencies
- Quick and lightweight execution

### Security Measures
- Secure token management
- GitHub API rate limit awareness
- Minimal personal information exposure
