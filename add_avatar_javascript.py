import re

# Read the profile template
with open('templates/profile.html', 'r') as f:
    content = f.read()

# Add avatar selection JavaScript before the closing script tag
avatar_javascript = '''
    // Avatar selection functionality
    document.getElementById('select-avatar-btn').addEventListener('click', function() {
        loadAvatars();
        document.getElementById('avatar-modal').classList.remove('hidden');
    });
    
    document.getElementById('close-avatar-modal').addEventListener('click', function() {
        document.getElementById('avatar-modal').classList.add('hidden');
    });
    
    // Close modal when clicking outside
    document.getElementById('avatar-modal').addEventListener('click', function(e) {
        if (e.target === this) {
            this.classList.add('hidden');
        }
    });
    
    async function loadAvatars() {
        try {
            const response = await fetch('/api/profile/avatars');
            const data = await response.json();
            
            if (data.success) {
                const avatarGrid = document.getElementById('avatar-grid');
                avatarGrid.innerHTML = '';
                
                data.avatars.forEach(avatar => {
                    const avatarElement = document.createElement('div');
                    avatarElement.className = 'text-center cursor-pointer p-2 rounded-lg hover:bg-gray-50 transition-colors';
                    avatarElement.innerHTML = `
                        <div class="w-16 h-16 rounded-full overflow-hidden mx-auto mb-2 border-2 ${data.current_avatar === avatar.path ? 'border-ki-green-500' : 'border-gray-200'}">
                            <img src="{{ url_for('static', filename='') }}${avatar.path}" 
                                 alt="${avatar.name}" 
                                 class="w-full h-full object-cover"
                                 onerror="this.src='{{ url_for('static', filename='assets/avatars/default-avatar.png') }}'">
                        </div>
                        <p class="text-xs text-gray-600">${avatar.name}</p>
                    `;
                    
                    avatarElement.addEventListener('click', () => selectAvatar(avatar.id));
                    avatarGrid.appendChild(avatarElement);
                });
            }
        } catch (error) {
            console.error('Error loading avatars:', error);
            showToast('Failed to load avatars', 'error');
        }
    }
    
    async function selectAvatar(avatarId) {
        try {
            showLoading();
            
            const response = await fetch('/api/profile/select-avatar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ avatar_id: avatarId })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update the profile image display
                const profileImageContainer = document.getElementById('profile-image');
                profileImageContainer.innerHTML = `<img src="${data.image_url}" alt="Profile Image" class="w-full h-full object-cover">`;
                
                // Hide remove button for avatars
                document.getElementById('remove-image-btn').classList.add('hidden');
                
                // Close modal
                document.getElementById('avatar-modal').classList.add('hidden');
                
                showToast('Avatar selected successfully!', 'success');
            } else {
                showToast(data.message || 'Failed to select avatar', 'error');
            }
        } catch (error) {
            console.error('Error selecting avatar:', error);
            showToast('Failed to select avatar', 'error');
        } finally {
            hideLoading();
        }
    }
'''

# Find the end of the script section and add the avatar JavaScript
pattern = r'    }\);\n</script>'
replacement = r'    });\n' + avatar_javascript + r'\n</script>'

# Apply the replacement
new_content = re.sub(pattern, replacement, content)

# Write the updated content back
with open('templates/profile.html', 'w') as f:
    f.write(new_content)

print("Avatar JavaScript functionality added!")
