import re

# Read the navigation template
with open('templates/components/navigation.html', 'r') as f:
    content = f.read()

# Replace the profile image logic with fallback
# Desktop navigation
content = re.sub(
    r'{% if current_user\.profile_image %}\s*<img src="{{ url_for\(\'static\', filename=current_user\.profile_image\) }}"\s+alt="Profile"\s+class="w-full h-full object-cover">\s*{% else %}\s*<div class="w-full h-full bg-gradient-to-br from-ki-green-500 to-ki-green-600 flex items-center justify-center">\s*<svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">\s*<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>\s*</svg>\s*</div>\s*{% endif %}',
    '<img src="{{ url_for(\'static\', filename=current_user.profile_image) if current_user.profile_image and current_user.profile_image != \'uploads/profile_images/default-profile.png\' else url_for(\'static\', filename=\'uploads/profile_images/default-profile.png\') }}" alt="Profile" class="w-full h-full object-cover" onerror="this.src=\'{{ url_for(\'static\', filename=\'uploads/profile_images/default-profile.png\') }}\'">',
    content
)

# Mobile navigation
content = re.sub(
    r'{% if current_user\.profile_image %}\s*<img src="{{ url_for\(\'static\', filename=current_user\.profile_image\) }}"\s+alt="Profile"\s+class="w-full h-full object-cover">\s*{% else %}\s*<div class="w-full h-full bg-gradient-to-br from-ki-green-500 to-ki-green-600 flex items-center justify-center">\s*<svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">\s*<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>\s*</svg>\s*</div>\s*{% endif %}',
    '<img src="{{ url_for(\'static\', filename=current_user.profile_image) if current_user.profile_image and current_user.profile_image != \'uploads/profile_images/default-profile.png\' else url_for(\'static\', filename=\'uploads/profile_images/default-profile.png\') }}" alt="Profile" class="w-full h-full object-cover" onerror="this.src=\'{{ url_for(\'static\', filename=\'uploads/profile_images/default-profile.png\') }}\'">',
    content
)

# Write the updated content back
with open('templates/components/navigation.html', 'w') as f:
    f.write(content)

print("Navigation template updated with profile image fallback!")
