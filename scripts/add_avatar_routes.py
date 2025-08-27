import re

# Read the app.py file
with open('app.py', 'r') as f:
    content = f.read()

# Add the avatar selection route after remove_profile_image
avatar_route = '''
@app.route('/api/profile/select-avatar', methods=['POST'])
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

@app.route('/api/profile/avatars', methods=['GET'])
@login_required
def get_avatars():
    """Get available avatars"""
    avatars = get_available_avatars()
    return jsonify({
        'success': True,
        'avatars': avatars,
        'current_avatar': current_user.profile_image
    })

'''

# Find the end of remove_profile_image route and add the avatar routes
pattern = r'(def remove_profile_image\(\):.*?return jsonify\(\{\'success\': False, \'message\': \'Failed to remove image\'\}\)\n)'
replacement = r'\1' + avatar_route

# Apply the replacement
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write the updated content back
with open('app.py', 'w') as f:
    f.write(new_content)

print("Avatar routes added successfully!")
