"""
Ki Wellness - OAuth Utilities
=============================

This module provides OAuth utilities for handling Google OAuth
authentication and YouTube API integration.

Author: Ki Wellness Team
Version: 1.0
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from flask import session, request, current_app
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from ..models import db, User


class OAuthService:
    """Modular OAuth service for Google authentication"""
    
    def __init__(self):
        self.scopes = {
            'youtube': ['https://www.googleapis.com/auth/youtube.readonly'],
            'profile': ['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email']
        }
        self.api_service_name = 'youtube'
        self.api_version = 'v3'
    
    def get_oauth_config(self) -> Dict[str, Any]:
        """Get OAuth configuration from environment variables"""
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:5001/youtube/oauth2callback')
        
        if not client_id or not client_secret:
            raise ValueError("Google OAuth credentials not configured")
        
        return {
            'web': {
                'client_id': client_id,
                'client_secret': client_secret,
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'redirect_uris': [redirect_uri]
            }
        }
    
    def create_flow(self, scope_type: str = 'youtube') -> Flow:
        """Create OAuth flow for specified scope"""
        config = self.get_oauth_config()
        scopes = self.scopes.get(scope_type, self.scopes['youtube'])
        
        flow = Flow.from_client_config(
            config,
            scopes=scopes,
            redirect_uri=config['web']['redirect_uris'][0]
        )
        
        return flow
    
    def initiate_auth(self, scope_type: str = 'youtube') -> Tuple[str, str]:
        """Initiate OAuth flow and return authorization URL and state"""
        if not session.get('user_id'):
            raise ValueError("User not logged in")
        
        flow = self.create_flow(scope_type)
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'  # Force consent to get refresh token
        )
        
        # Store state and flow in session
        session['oauth_state'] = state
        session['oauth_scope_type'] = scope_type
        
        return authorization_url, state
    
    def handle_callback(self, authorization_response: str) -> Dict[str, Any]:
        """Handle OAuth callback and return credentials"""
        if not session.get('user_id'):
            raise ValueError("User not logged in")
        
        scope_type = session.get('oauth_scope_type', 'youtube')
        flow = self.create_flow(scope_type)
        
        # Fetch token from authorization response
        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials
        
        # Store credentials in session
        session['oauth_credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
        
        # Clear OAuth state
        session.pop('oauth_state', None)
        session.pop('oauth_scope_type', None)
        
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'expiry': credentials.expiry
        }
    
    def get_credentials(self) -> Optional[Credentials]:
        """Get stored OAuth credentials"""
        if 'oauth_credentials' not in session:
            return None
        
        try:
            creds_dict = session['oauth_credentials'].copy()
            if creds_dict.get('expiry'):
                creds_dict['expiry'] = datetime.fromisoformat(creds_dict['expiry'])
            
            credentials = Credentials.from_authorized_user_info(creds_dict)
            
            # Check if token is expired and refresh if needed
            if credentials.expired and credentials.refresh_token:
                self.refresh_token()
                return self.get_credentials()
            
            return credentials
        except Exception as e:
            print(f"Error getting credentials: {e}")
            return None
    
    def refresh_token(self) -> bool:
        """Refresh OAuth access token"""
        if 'oauth_credentials' not in session:
            return False
        
        try:
            credentials = self.get_credentials()
            if not credentials or not credentials.refresh_token:
                return False
            
            # Refresh the token
            credentials.refresh(request)
            
            # Update session with new credentials
            session['oauth_credentials'] = {
                'token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_uri': credentials.token_uri,
                'client_id': credentials.client_id,
                'client_secret': credentials.client_secret,
                'scopes': credentials.scopes,
                'expiry': credentials.expiry.isoformat() if credentials.expiry else None
            }
            
            return True
        except Exception as e:
            print(f"Error refreshing token: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated with OAuth"""
        return 'oauth_credentials' in session and self.get_credentials() is not None
    
    def logout(self) -> None:
        """Clear OAuth credentials from session"""
        session.pop('oauth_credentials', None)
        session.pop('oauth_state', None)
        session.pop('oauth_scope_type', None)


class YouTubeService:
    """YouTube API service using OAuth authentication"""
    
    def __init__(self, oauth_service: OAuthService):
        self.oauth_service = oauth_service
        self.api_service_name = 'youtube'
        self.api_version = 'v3'
    
    def get_service(self):
        """Get YouTube API service instance"""
        credentials = self.oauth_service.get_credentials()
        if not credentials:
            return None
        
        try:
            service = build(self.api_service_name, self.api_version, credentials=credentials)
            return service
        except Exception as e:
            print(f"Error creating YouTube service: {e}")
            return None
    
    def get_playlists(self) -> Dict[str, Any]:
        """Get user's YouTube playlists"""
        service = self.get_service()
        if not service:
            return {'success': False, 'error': 'YouTube not authenticated'}
        
        try:
            request_playlists = service.playlists().list(
                part='snippet',
                mine=True,
                maxResults=50
            )
            
            playlists_response = request_playlists.execute()
            
            playlists = []
            for item in playlists_response.get('items', []):
                playlist = {
                    'id': item['id'],
                    'name': item['snippet']['title'],
                    'description': item['snippet'].get('description', ''),
                    'thumbnail': item['snippet'].get('thumbnails', {}).get('default', {}).get('url', ''),
                    'video_count': item['snippet'].get('videoCount', 0)
                }
                playlists.append(playlist)
            
            return {
                'success': True,
                'playlists': playlists
            }
            
        except HttpError as e:
            print(f"YouTube API error: {e}")
            return {'success': False, 'error': 'Failed to fetch playlists'}
        except Exception as e:
            print(f"Error fetching playlists: {e}")
            return {'success': False, 'error': 'Internal server error'}
    
    def get_playlist_videos(self, playlist_id: str) -> Dict[str, Any]:
        """Get videos from a specific playlist"""
        service = self.get_service()
        if not service:
            return {'success': False, 'error': 'YouTube not authenticated'}
        
        try:
            request_videos = service.playlistItems().list(
                part='snippet',
                playlistId=playlist_id,
                maxResults=50
            )
            
            videos_response = request_videos.execute()
            
            videos = []
            for item in videos_response.get('items', []):
                snippet = item['snippet']
                video = {
                    'id': snippet['resourceId']['videoId'],
                    'title': snippet['title'],
                    'description': snippet.get('description', ''),
                    'thumbnail': snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
                    'duration': snippet.get('duration', ''),
                    'published_at': snippet.get('publishedAt', '')
                }
                videos.append(video)
            
            return {
                'success': True,
                'videos': videos,
                'playlist_id': playlist_id
            }
            
        except HttpError as e:
            print(f"YouTube API error: {e}")
            return {'success': False, 'error': 'Failed to fetch videos'}
        except Exception as e:
            print(f"Error fetching videos: {e}")
            return {'success': False, 'error': 'Internal server error'}


# Global service instances
oauth_service = OAuthService()
youtube_service = YouTubeService(oauth_service)
