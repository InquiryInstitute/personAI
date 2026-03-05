"""
Web search integration for personAI
Handles web search and content retrieval
"""
from typing import List, Dict
import logging
import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WebConnector:
    """Connector for web search and scraping"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; PersonAI/0.1; +https://github.com/InquiryInstitute/PersonAI)'
        }
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Search the web for a query
        Note: This is a simple implementation. For production, consider using
        a proper search API like Google Custom Search, Bing, or DuckDuckGo
        """
        # TODO: Implement actual web search API integration
        logger.warning("Web search not fully implemented. Use a search API for production.")
        return []
    
    async def fetch_url(self, url: str) -> str:
        """Fetch and extract text content from a URL"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=10) as response:
                    if response.status != 200:
                        raise ValueError(f"HTTP {response.status} error fetching {url}")
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # Get text
                    text = soup.get_text()
                    
                    # Clean up whitespace
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = ' '.join(chunk for chunk in chunks if chunk)
                    
                    return text
                    
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {e}")
            raise
    
    async def extract_links(self, url: str) -> List[Dict[str, str]]:
        """Extract all links from a webpage"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=10) as response:
                    if response.status != 200:
                        raise ValueError(f"HTTP {response.status} error fetching {url}")
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    links = []
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        text = link.get_text(strip=True)
                        if href.startswith('http'):
                            links.append({
                                'url': href,
                                'text': text or href
                            })
                    
                    return links
                    
        except Exception as e:
            logger.error(f"Error extracting links from {url}: {e}")
            return []
