"""
Google Drive API client for uploading files
"""
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import pickle
from src.core import config


# Scopes required for Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.file']


class GoogleDriveClient:
    """Client for interacting with Google Drive API"""
    
    def __init__(self):
        """Initialize Google Drive client with authentication"""
        self.credentials_path = config.GOOGLE_DRIVE_CREDENTIALS_PATH
        self.token_path = os.path.join(os.path.dirname(self.credentials_path), 'token.pickle')
        self.service = self._authenticate()
    
    def _authenticate(self):
        """Authenticate and return Google Drive service"""
        creds = None
        
        # Load existing token if available
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Google Drive credentials not found at {self.credentials_path}. "
                        "Please download OAuth 2.0 credentials from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save credentials for next run
            os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        return build('drive', 'v3', credentials=creds)
    
    def create_folder(self, folder_name: str, parent_folder_id: str = None) -> str:
        """
        Create a folder in Google Drive

        Args:
            folder_name: Name of the folder to create
            parent_folder_id: Optional parent folder ID (uses config default if not provided)

        Returns:
            Folder ID of the created folder
        """
        parent_folder_id = parent_folder_id or config.GOOGLE_DRIVE_FOLDER_ID

        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        if parent_folder_id:
            file_metadata['parents'] = [parent_folder_id]

        try:
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()

            return folder.get('id')
        except HttpError as error:
            print(f"An error occurred while creating folder: {error}")
            raise

    def find_folder(self, folder_name: str, parent_folder_id: str = None) -> str:
        """
        Find a folder by name in Google Drive

        Args:
            folder_name: Name of the folder to find
            parent_folder_id: Optional parent folder ID to search in

        Returns:
            Folder ID if found, None otherwise
        """
        parent_folder_id = parent_folder_id or config.GOOGLE_DRIVE_FOLDER_ID

        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_folder_id:
            query += f" and '{parent_folder_id}' in parents"

        try:
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            files = results.get('files', [])
            return files[0]['id'] if files else None
        except HttpError as error:
            print(f"An error occurred while searching for folder: {error}")
            return None

    def get_or_create_folder(self, folder_name: str, parent_folder_id: str = None) -> str:
        """
        Get existing folder or create if it doesn't exist

        Args:
            folder_name: Name of the folder
            parent_folder_id: Optional parent folder ID

        Returns:
            Folder ID
        """
        folder_id = self.find_folder(folder_name, parent_folder_id)
        if folder_id:
            return folder_id
        return self.create_folder(folder_name, parent_folder_id)

    def upload_file(self, file_path: str, folder_id: str = None, file_name: str = None) -> str:
        """
        Upload a file to Google Drive

        Args:
            file_path: Path to the file to upload
            folder_id: Optional folder ID to upload to (uses config default if not provided)
            file_name: Optional custom filename

        Returns:
            File ID of the uploaded file
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        folder_id = folder_id or config.GOOGLE_DRIVE_FOLDER_ID
        file_name = file_name or os.path.basename(file_path)

        file_metadata = {
            'name': file_name,
        }

        if folder_id:
            file_metadata['parents'] = [folder_id]

        media = MediaFileUpload(file_path, resumable=True)

        try:
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            return file.get('id')
        except HttpError as error:
            print(f"An error occurred: {error}")
            raise

