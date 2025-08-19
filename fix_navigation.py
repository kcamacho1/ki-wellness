import re

# Read the navigation template
with open('templates/components/navigation.html', 'r') as f:
    content = f.read()

# Replace the profile image sections with fallback logic
# Desktop navigation - first occurrence
content = re.sub(
    r'<div class="w-8 h-8 rounded-full overflow-hidden flex items-center justify-center">\s*{% if current_user\.profile_image %}\s*<img src="{{ url_for\(\'static\', filename=current_user\.profile_image\) }}"\s+alt="Profile"\s+class="w-full h-full object-cover">\s*{% else %}\s*<div class="w-full h-full bg-gradient-to-br from-ki-green-500 to-ki-green-600 flex items-center justify-center">\s*<svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">\s*<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>\s*</svg>\s*</div>\s*{% endif %}\s*</div>',
    '<div class="w-8 h-8 rounded-full overflow-hidden flex items-center justify-center">\n                                <img src="{{ url_for(\'static\', filename=current_user.profile_image) if current_user.profile_image else url_for(\'static\', filename=\'uploads/profile_images/default-profile.png\') }}" \n                                     alt="Profile" \n                                     class="w-full h-full object-cover"\n                                     onerror="this.src=\'{{ url_for(\'static\', filename=\'uploads/profile_images/default-profile.png\') }}\'">\n                            </div>',
    content,
    count=1
)

# Mobile navigation - second occurrence
content = re.sub(
    r'<div class="w-8 h-8 rounded-full overflow-hidden flex items-center justify-center">\s*{% if current_user\.profile_image %}\s*<img src="{{ url_for\(\'static\', filename=current_user\.profile_image\) }}"\s+alt="Profile"\s+class="w-full h-full object-cover">\s*{% else %}\s*<div class="w-full h-full bg-gradient-to-br from-ki-green-500 to-ki-green-600 flex items-center justify-center">\s*<svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">\s*<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>\s*</svg>\s*</div>\s*{% endif %}\s*</div>',
    '<div class="w-8 h-8 rounded-full overflow-hidden flex items-center justify-center">\n                        <img src="{{ url_for(\'static\', filename=current_user.profile_image) if current_user.profile_image else url_for(\'static\', filename=\'uploads/profile_images/default-profile.png\') }}" \n                             alt="Profile" \n                             class="w-full h-full object-cover"\n                             onerror="this.src=\'{{ url_for(\'static\', filename=\'uploads/profile_images/default-profile.png\') }}\'">\n                    </div>',
    content,
    count=1
)

# Write the updated content back
with open('templates/components/navigation.html', 'w') as f:
    f.write(content)

print("Navigation template updated with profile image fallback!")
