"""
GitHub integration for personAI
Handles repository access and file retrieval
"""
from typing import List, Dict
import os
from github import Github, GithubException
import logging

logger = logging.getLogger(__name__)


class GitHubConnector:
    """Connector for GitHub API with safety controls"""
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.username = os.getenv("GITHUB_USER")
        self.allowed_repos = self._parse_allowed_repos()
        self.read_only = os.getenv("READ_ONLY_MODE", "true").lower() == "true"
        
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
            
        self.client = Github(self.token)
        
    def _parse_allowed_repos(self) -> List[str]:
        """Parse allowed repositories from environment"""
        repos = os.getenv("ALLOWED_REPOS", "")
        if not repos:
            return []
        return [r.strip() for r in repos.split(",")]
    
    def _check_repo_allowed(self, repo_name: str) -> bool:
        """Check if repository access is allowed"""
        if not self.allowed_repos:
            return True  # If no restrictions set, allow all
        return repo_name in self.allowed_repos
    
    async def list_repositories(self) -> List[Dict[str, str]]:
        """List accessible repositories"""
        try:
            user = self.client.get_user()
            repos = []
            for repo in user.get_repos():
                if self._check_repo_allowed(repo.name):
                    repos.append({
                        "name": repo.name,
                        "full_name": repo.full_name,
                        "description": repo.description or "",
                        "private": repo.private
                    })
            return repos
        except GithubException as e:
            logger.error(f"Error listing repositories: {e}")
            return []
    
    async def get_file_content(self, repo_name: str, file_path: str, branch: str = "main") -> str:
        """Get content of a specific file from a repository"""
        if not self._check_repo_allowed(repo_name):
            raise PermissionError(f"Access to repository {repo_name} is not allowed")
        
        try:
            repo = self.client.get_repo(f"{self.username}/{repo_name}")
            content = repo.get_contents(file_path, ref=branch)
            
            if isinstance(content, list):
                raise ValueError(f"{file_path} is a directory, not a file")
                
            return content.decoded_content.decode("utf-8")
        except GithubException as e:
            logger.error(f"Error getting file content: {e}")
            raise
    
    async def search_code(self, query: str) -> List[Dict[str, str]]:
        """Search code across allowed repositories"""
        try:
            results = []
            for repo_name in self.allowed_repos if self.allowed_repos else []:
                search_query = f"{query} repo:{self.username}/{repo_name}"
                code_results = self.client.search_code(search_query)
                
                for item in code_results[:10]:  # Limit results
                    results.append({
                        "repository": item.repository.full_name,
                        "path": item.path,
                        "url": item.html_url
                    })
            
            return results
        except GithubException as e:
            logger.error(f"Error searching code: {e}")
            return []
