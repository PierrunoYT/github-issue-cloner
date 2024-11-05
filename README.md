# GitHub Issue Cloner

A Python web application to clone GitHub issues from one repository to your forked repository, with both CLI and web interface support.

## 🌟 Features

- Web GUI for easy issue cloning
- CLI support (via `issue_cloner.py`)
- Automatically detect and use your forked repository
- Preserve original issue details
- Add reference to original issue
- Automatic fork detection

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
- Ensure you have `venv` module installed
  - On Windows: `python -m pip install virtualenv`
  - On macOS/Linux: `python3 -m pip install virtualenv`
- If activation fails, check Python installation
- Verify Python version with `python --version`

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

3. Enter your GitHub Personal Access Token and the issue URL you want to clone

### CLI Interface

Run the script:
```bash
python issue_cloner.py
```

When prompted:
1. Paste a GitHub issue URL (e.g., `https://github.com/owner/repo/issues/123`)

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

Project Link: [https://github.com/PierrunoYT/github-issue-cloner](https://github.com/PierrunoYT/github-issue-cloner)
