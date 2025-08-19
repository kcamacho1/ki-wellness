import re

# Read the app.py file
with open('app.py', 'r') as f:
    content = f.read()

# Add the get_available_avatars function after get_profile_image_url
avatar_function = '''
def get_available_avatars():
    """Get list of available avatar options"""
    avatars = [
        {'id': 'default', 'name': 'Default', 'path': 'assets/avatars/default-avatar.png'},
        {'id': 'man1', 'name': 'Man 1', 'path': 'assets/avatars/man1.png'},
        {'id': 'man2', 'name': 'Man 2', 'path': 'assets/avatars/man2.png'},
        {'id': 'man3', 'name': 'Man 3', 'path': 'assets/avatars/man3.png'},
        {'id': 'man4', 'name': 'Man 4', 'path': 'assets/avatars/man4.png'},
        {'id': 'man5', 'name': 'Man 5', 'path': 'assets/avatars/man5.png'},
        {'id': 'girl1', 'name': 'Woman 1', 'path': 'assets/avatars/girl1.png'},
        {'id': 'girl2', 'name': 'Woman 2', 'path': 'assets/avatars/girl2.png'},
        {'id': 'girl3', 'name': 'Woman 3', 'path': 'assets/avatars/girl3.png'},
        {'id': 'girl4', 'name': 'Woman 4', 'path': 'assets/avatars/girl4.png'},
        {'id': 'girl5', 'name': 'Woman 5', 'path': 'assets/avatars/girl5.png'}
    ]
    return avatars

'''

# Find the end of get_profile_image_url function and add the avatar function
pattern = r'(def get_profile_image_url\(profile_image_path\):.*?return url_for\(\'static\', filename=\'assets/avatars/default-avatar\.png\'\)\n)'
replacement = r'\1' + avatar_function

# Apply the replacement
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write the updated content back
with open('app.py', 'w') as f:
    f.write(new_content)

print("Avatar functions added successfully!")
