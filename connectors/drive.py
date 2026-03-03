"""
Google Drive integration for personAI
Handles Drive access and document retrieval
"""
from typing import List, Dict, Optional
import os
import logging
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GoogleDriveConnector:
    """Connector for Google Drive API with safety controls"""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    def __init__(self):
        self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        self.allowed_folders = self._parse_allowed_folders()
        self.read_only = True  # Always read-only for Drive
        
        if not self.credentials_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable is required")
        
        self.service = self._build_service()
    
    def _parse_allowed_folders(self) -> List[str]:
        """Parse allowed folders from environment"""
        folders = os.getenv("ALLOWED_DRIVE_FOLDERS", "")
        if not folders:
            return []
        return [f.strip() for f in folders.split(",")]
    
    def _build_service(self):
        """Build Google Drive API service"""
        try:
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            logger.error(f"Error building Drive service: {e}")
            raise
    
    def _check_folder_allowed(self, folder_id: str) -> bool:
        """Check if folder access is allowed"""
        if not self.allowed_folders:
            return True
        return folder_id in self.allowed_folders
    
    async def list_files(self, folder_id: Optional[str] = None, mime_type: Optional[str] = None) -> List[Dict[str, str]]:
        """List files in a folder"""
        folder_id = folder_id or self.folder_id
        
        if not self._check_folder_allowed(folder_id):
            raise PermissionError(f"Access to folder {folder_id} is not allowed")
        
        try:
            query = f"'{folder_id}' in parents and trashed=false"
            if mime_type:
                query += f" and mimeType='{mime_type}'"
            
            results = self.service.files().list(
                q=query,
                fields="files(id, name, mimeType, modifiedTime, webViewLink)",
                pageSize=100
            ).execute()
            
            return results.get('files', [])
        except HttpError as e:
            logger.error(f"Error listing files: {e}")
            return []
    
    async def get_file_content(self, file_id: str) -> str:
        """Get content of a file (text-based files only)"""
        try:
            # Get file metadata to check mime type
            file = self.service.files().get(fileId=file_id, fields='mimeType,name').execute()
            mime_type = file.get('mimeType')
            
            # Handle Google Docs types
            if mime_type == 'application/vnd.google-apps.document':
                export_mime = 'text/plain'
                content = self.service.files().export(fileId=file_id, mimeType=export_mime).execute()
                return content.decode('utf-8')
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                export_mime = 'text/csv'
                content = self.service.files().export(fileId=file_id, mimeType=export_mime).execute()
                return content.decode('utf-8')
            else:
                # For other text files
                content = self.service.files().get_media(fileId=file_id).execute()
                return content.decode('utf-8')
                
        except HttpError as e:
            logger.error(f"Error getting file content: {e}")
            raise
        except UnicodeDecodeError:
            raise ValueError(f"File is not a text-based document")
    
    async def search_files(self, query: str, folder_id: Optional[str] = None) -> List[Dict[str, str]]:
        """Search files by name"""
        folder_id = folder_id or self.folder_id
        
        if not self._check_folder_allowed(folder_id):
            raise PermissionError(f"Access to folder {folder_id} is not allowed")
        
        try:
            search_query = f"'{folder_id}' in parents and name contains '{query}' and trashed=false"
            
            results = self.service.files().list(
                q=search_query,
                fields="files(id, name, mimeType, modifiedTime, webViewLink)",
                pageSize=50
            ).execute()
            
            return results.get('files', [])
        except HttpError as e:
            logger.error(f"Error searching files: {e}")
            return []
