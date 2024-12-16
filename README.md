# GitHub Issue Cloner

A Python web application to clone GitHub issues from one repository to your forked repository, with both CLI and web interface support.

## 🌟 Features

- Web GUI for easy issue cloning with rate limiting protection
- CLI support (via `issue_cloner.py`)
- Automatically detect and use your forked repository
- Preserve original issue details including labels
- Add reference to original issue
- Automatic fork detection
- Security features:
  * Rate limiting protection
  * Input sanitization
  * Request size limits
  * CORS support

## 🛠 Prerequisites

- Python 3.6+
- GitHub Personal Access Token with 'repo' scope
- A GitHub account
- Forked repository (or ability to fork)
- Internet connection

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/PierrunoYT/github-issue-cloner.git
cd github-issue-cloner
```

2. Create a virtual environment:

### On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### On macOS and Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Troubleshooting Virtual Environment:
- Ensure you have Python 3.3 or above, which includes the `venv` module.
- If you encounter issues with `venv`, you can use `virtualenv` as an alternative:
  - Install it using `pip install virtualenv`
  - Create a virtual environment with `virtualenv venv`
  - Activate it using the same commands as above.
- Verify your Python version with `python --version`.

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## 🔧 Configuration

1. Create a `.env` file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your GitHub Personal Access Token:
   - Go to [GitHub Token Settings](https://github.com/settings/tokens)
   - Generate a new token with 'repo' scope
   - Copy the token into `.env`

## 💡 Usage

### Web Interface

1. Start the Flask application:
```bash
python app.py
```

2. Open a web browser and navigate to `http://localhost:5000`

3. In the web interface:
   - Enter the URL of the original GitHub issue you want to clone
   - Enter the URL of your forked repository
   - Click "Clone Issue" to create a copy of the issue in your forked repository
   - The application will:
     * Validate the issue and repository URLs
     * Check if issues are enabled in your forked repository
     * Copy the issue title, description, and labels
     * Add a reference to the original issue
     * Create a new issue in your forked repository

### CLI Interface

Run the script:
```bash
python issue_cloner.py
```

When prompted:
1. Paste a GitHub issue URL (e.g., `https://github.com/owner/repo/issues/123`)
2. The script will automatically:
   - Validate your GitHub token
   - Check for and use your forked repository
   - Enable issues if needed (with your permission)
   - Clone the issue with all details

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🐛 Issues

Report issues [here](https://github.com/PierrunoYT/github-issue-cloner/issues).

## 🔍 Additional Notes

- Ensure you have the necessary permissions to clone and create issues in the target repository
- The application handles rate limiting and authentication securely
- Features rate limiting protection (100 requests per day, 10 per minute)
- Supports both open and closed issues
- Preserves issue labels and state
- Handles locked issues appropriately
- Prevents duplicate issues in target repository

Project Link: [https://github.com/PierrunoYT/github-issue-cloner](https://github.com/PierrunoYT/github-issue-cloner)

Last updated: December 16, 2024
