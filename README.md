# personAI

A secure personal AI assistant that interacts with your own data across GitHub repositories, Google Shared Drive, and the web. Built with safety and privacy in mind.

## Overview

personAI enables you to ask questions and interact with your personal data using AI, similar to OpenClaw but with enhanced security controls. Your data stays under your control while being accessible to your personal AI assistant.

## Features

- **GitHub Integration**: Query and interact with files in your personal GitHub repositories
- **Google Drive Integration**: Access and search documents in your Google Shared Drive
- **Web Search**: Retrieve information from the web to augment your personal knowledge base
- **Privacy First**: All data access is scoped to your authenticated accounts
- **Secure by Design**: Built-in safety controls and permission management

## Deployment Options

### GitHub Codespaces
Deploy and run personAI directly in GitHub Codespaces for a zero-setup development environment.

### Google Cloud Run (GCR)
Deploy personAI as a serverless application on Google Cloud Run for production use.

## Getting Started

### Prerequisites

- GitHub account with personal repositories
- Google Cloud account (for Drive access and GCR deployment)
- Python 3.11+

### Local Development

```bash
# Clone the repository
git clone https://github.com/InquiryInstitute/personAI.git
cd personAI

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your API keys and credentials

# Run locally
python main.py
```

### Deploy to Codespaces

Click the "Code" button on GitHub and select "Create codespace on main" to launch a development environment with all dependencies pre-installed.

### Deploy to Google Cloud Run

```bash
# Build and deploy
gcloud run deploy personai \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Architecture

personAI uses:
- **LangChain** for AI orchestration and retrieval augmented generation (RAG)
- **GitHub API** for repository access
- **Google Drive API** for file access
- **Vector database** for efficient semantic search across your documents
- **Safety guardrails** to prevent unintended actions

## Security

- All API credentials are stored securely and never logged
- Fine-grained permission controls for data access
- Read-only mode by default for file operations
- Audit logging for all AI actions

## Certificate Program

This project is part of the [Sovereign AI Certificate](https://github.com/InquiryInstitute/sovereign) program offered by Inquiry Institute.

## License

MIT License - see LICENSE file for details
