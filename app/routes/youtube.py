"""
Ki Wellness - YouTube API Routes
================================

This module handles YouTube API integration for the exercise page,
using the modular OAuth service.

Author: Ki Wellness Team
Version: 1.0
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for

try:
    from ..utils.oauth_utils import oauth_service, youtube_service
    YOUTUBE_AVAILABLE = True
except RuntimeError:
    YOUTUBE_AVAILABLE = False
    oauth_service = None
    youtube_service = None

# Create blueprint
youtube_bp = Blueprint('youtube', __name__)

@youtube_bp.route('/youtube/auth')
def youtube_auth():
    """Initiate YouTube OAuth flow"""
    if not YOUTUBE_AVAILABLE:
        return jsonify({'success': False, 'error': 'YouTube integration not available'}), 503
    
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'User not logged in'}), 401
    
    try:
        authorization_url, state = oauth_service.initiate_auth('youtube')
        
        return jsonify({
            'success': True,
            'auth_url': authorization_url
        })
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 401
    except Exception as e:
        print(f"Error initiating YouTube auth: {e}")
        return jsonify({'success': False, 'error': 'Failed to initiate authentication'}), 500

@youtube_bp.route('/youtube/oauth2callback')
def youtube_oauth2callback():
    """Handle OAuth callback from Google"""
    if not YOUTUBE_AVAILABLE:
        return jsonify({'success': False, 'error': 'YouTube integration not available'}), 503
    
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'User not logged in'}), 401
    
    try:
        # Handle OAuth callback
        credentials = oauth_service.handle_callback(request.url)
        
        return redirect(url_for('static.exercise'))
        
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 401
    except Exception as e:
        print(f"Error in OAuth callback: {e}")
        return jsonify({'success': False, 'error': 'Authentication failed'}), 500

@youtube_bp.route('/youtube/playlists')
def get_playlists():
    """Get user's YouTube playlists"""
    if not YOUTUBE_AVAILABLE:
        return jsonify({'success': False, 'error': 'YouTube integration not available'}), 503
    
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'User not logged in'}), 401
    
    result = youtube_service.get_playlists()
    return jsonify(result)

@youtube_bp.route('/youtube/playlist/<playlist_id>/videos')
def get_playlist_videos(playlist_id):
    """Get videos from a specific playlist"""
    if not YOUTUBE_AVAILABLE:
        return jsonify({'success': False, 'error': 'YouTube integration not available'}), 503
    
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'User not logged in'}), 401
    
    result = youtube_service.get_playlist_videos(playlist_id)
    return jsonify(result)

@youtube_bp.route('/youtube/auth/status')
def youtube_auth_status():
    """Check if user is authenticated with YouTube"""
    if not YOUTUBE_AVAILABLE:
        return jsonify({'success': False, 'error': 'YouTube integration not available'}), 503
    
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'User not logged in'}), 401
    
    is_authenticated = oauth_service.is_authenticated()
    
    return jsonify({
        'success': True,
        'authenticated': is_authenticated
    })

@youtube_bp.route('/youtube/logout')
def youtube_logout():
    """Logout from YouTube (clear credentials)"""
    if not YOUTUBE_AVAILABLE:
        return jsonify({'success': False, 'error': 'YouTube integration not available'}), 503
    
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'User not logged in'}), 401
    
    oauth_service.logout()
    
    return jsonify({
        'success': True,
        'message': 'Logged out from YouTube'
    })

@youtube_bp.route('/youtube/refresh-token')
def refresh_youtube_token():
    """Refresh YouTube access token"""
    if not YOUTUBE_AVAILABLE:
        return jsonify({'success': False, 'error': 'YouTube integration not available'}), 503
    
    if not session.get('user_id'):
        return jsonify({'success': False, 'error': 'User not logged in'}), 401
    
    if not oauth_service.is_authenticated():
        return jsonify({'success': False, 'error': 'No credentials to refresh'}), 401
    
    try:
        success = oauth_service.refresh_token()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Token refreshed successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to refresh token'
            }), 500
        
    except Exception as e:
        print(f"Error refreshing token: {e}")
        return jsonify({'success': False, 'error': 'Failed to refresh token'}), 500
