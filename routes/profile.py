# Profile-related routes
import os
import uuid
from flask import Blueprint, request, jsonify, url_for
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from database import db
from utils.helpers import validate_password_strength

# Create blueprint
profile_bp = Blueprint('profile', __name__)

# Configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_image(file, user_id):
    """Save uploaded profile image and return the filename"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"profile_{user_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
        
        # Save to uploads directory
        upload_path = os.path.join('static', 'uploads', 'profiles', filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        file.save(upload_path)
        
        # Return relative path for database storage
        return f"uploads/profiles/{filename}"
    return None

def delete_profile_image(filename):
    """Delete profile image file"""
    if filename:
        try:
            filepath = os.path.join('static', filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Deleted profile image: {filepath}")
        except Exception as e:
            print(f"Error deleting profile image {filename}: {e}")

def get_profile_image_url(profile_image_path):
    """Get profile image URL with fallback to default image"""
    if not profile_image_path:
        return url_for('static', filename='assets/avatars/default-avatar.png')
    
    return url_for('static', filename=profile_image_path)

def get_available_avatars():
    """Get list of available avatar options"""
    avatars = [
        {'id': 'default', 'name': 'Default', 'path': 'assets/avatars/default-avatar.png'},
        {'id': 'man1', 'name': 'Man 1', 'path': 'assets/avatars/man1.png'},
        {'id': 'man2', 'name': 'Man 2', 'path': 'assets/avatars/man2.png'},
        {'id': 'man3', 'name': 'Man 3', 'path': 'assets/avatars/man3.png'},
        {'id': 'man4', 'name': 'Man 4', 'path': 'assets/avatars/man4.png'},
        {'id': 'woman1', 'name': 'Woman 1', 'path': 'assets/avatars/woman1.png'},
        {'id': 'woman2', 'name': 'Woman 2', 'path': 'assets/avatars/woman2.png'},
        {'id': 'woman3', 'name': 'Woman 3', 'path': 'assets/avatars/woman3.png'},
        {'id': 'woman4', 'name': 'Woman 4', 'path': 'assets/avatars/woman4.png'},
        {'id': 'woman5', 'name': 'Woman 5', 'path': 'assets/avatars/woman5.png'},
        {'id': 'woman6', 'name': 'Woman 6', 'path': 'assets/avatars/woman6.png'},
        {'id': 'person1', 'name': 'Person 1', 'path': 'assets/avatars/person1.png'},
        {'id': 'person2', 'name': 'Person 2', 'path': 'assets/avatars/person2.png'},
        {'id': 'person3', 'name': 'Person 3', 'path': 'assets/avatars/person3.png'},
        {'id': 'person4', 'name': 'Person 4', 'path': 'assets/avatars/person4.png'},
        {'id': 'person5', 'name': 'Person 5', 'path': 'assets/avatars/person5.png'},
        {'id': 'person6', 'name': 'Person 6', 'path': 'assets/avatars/person6.png'},
    ]
    
    # Add full URLs for each avatar
    for avatar in avatars:
        avatar['url'] = url_for('static', filename=avatar['path'])
    
    return avatars

@profile_bp.route('/api/profile', methods=['GET', 'POST'])
@login_required
def profile_api():
    if request.method == 'POST':
        data = request.get_json()
        
        current_user.name = data['name']
        current_user.age = data.get('age')
        current_user.weight = data.get('weight')
        current_user.height = data.get('height')
        current_user.health_goals = data.get('health_goals')
        current_user.ailments_concerns = data.get('ailments_concerns')
        
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({
        'success': True,
        'data': {
            'name': current_user.name,
            'age': current_user.age,
            'weight': current_user.weight,
            'height': current_user.height,
            'health_goals': current_user.health_goals,
            'ailments_concerns': current_user.ailments_concerns,
            'profile_image': current_user.profile_image,
            'is_admin': current_user.is_admin
        }
    })

@profile_bp.route('/api/profile/upload-image', methods=['POST'])
@login_required
def upload_profile_image():
    """Upload profile image"""
    if 'profile_image' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    
    file = request.files['profile_image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WebP'})
    
    try:
        # Delete old profile image if exists
        if current_user.profile_image:
            delete_profile_image(current_user.profile_image)
        
        # Save new profile image
        filename = save_profile_image(file, current_user.id)
        if filename:
            current_user.profile_image = filename
            db.session.commit()
            return jsonify({
                'success': True, 
                'message': 'Profile image uploaded successfully',
                'image_url': url_for('static', filename=filename)
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to save image'})
            
    except Exception as e:
        print(f"Error uploading profile image: {e}")
        return jsonify({'success': False, 'message': 'Failed to upload image'})

@profile_bp.route('/api/profile/remove-image', methods=['POST'])
@login_required
def remove_profile_image():
    """Remove profile image"""
    try:
        if current_user.profile_image:
            delete_profile_image(current_user.profile_image)
            current_user.profile_image = None
            db.session.commit()
            return jsonify({'success': True, 'message': 'Profile image removed successfully'})
        else:
            return jsonify({'success': False, 'message': 'No profile image to remove'})
    except Exception as e:
        print(f"Error removing profile image: {e}")
        return jsonify({'success': False, 'message': 'Failed to remove image'})

@profile_bp.route('/api/profile/select-avatar', methods=['POST'])
@login_required
def select_avatar():
    """Select a predefined avatar"""
    data = request.get_json()
    avatar_id = data.get('avatar_id')
    
    if not avatar_id:
        return jsonify({'success': False, 'message': 'Avatar ID is required'})
    
    # Get available avatars
    avatars = get_available_avatars()
    selected_avatar = next((avatar for avatar in avatars if avatar['id'] == avatar_id), None)
    
    if not selected_avatar:
        return jsonify({'success': False, 'message': 'Invalid avatar selection'})
    
    try:
        # Delete old custom profile image if exists
        if current_user.profile_image and not current_user.profile_image.startswith('assets/avatars/'):
            delete_profile_image(current_user.profile_image)
        
        # Set the selected avatar
        current_user.profile_image = selected_avatar['path']
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Avatar selected successfully',
            'image_url': url_for('static', filename=selected_avatar['path'])
        })
        
    except Exception as e:
        print(f"Error selecting avatar: {e}")
        return jsonify({'success': False, 'message': 'Failed to select avatar'})

@profile_bp.route('/api/profile/avatars', methods=['GET'])
@login_required
def get_avatars():
    """Get available avatars"""
    avatars = get_available_avatars()
    return jsonify({
        'success': True,
        'avatars': avatars,
        'current_avatar': current_user.profile_image
    })

@profile_bp.route('/api/profile/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    data = request.get_json()
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    # Validate current password
    if not current_password:
        return jsonify({'success': False, 'message': 'Current password is required'})
    
    if not check_password_hash(current_user.password_hash, current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect'})
    
    # Validate new password
    if not new_password:
        return jsonify({'success': False, 'message': 'New password is required'})
    
    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'New passwords do not match'})
    
    # Validate password strength
    is_valid_password, password_error = validate_password_strength(new_password)
    if not is_valid_password:
        return jsonify({'success': False, 'message': password_error})
    
    # Update password
    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Password changed successfully'})
