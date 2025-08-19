import re

# Read the profile template
with open('templates/profile.html', 'r') as f:
    content = f.read()

# Replace the profile image section with avatar selection
new_profile_section = '''            <!-- Profile Image Section -->
            <div class="mb-8 text-center">
                <div class="relative inline-block">
                    <!-- Profile Image Display -->
                    <div id="profile-image-container" class="relative">
                        <div id="profile-image" class="w-24 h-24 rounded-full overflow-hidden mx-auto mb-4 border-4 border-gray-200">
                            <img src="{{ url_for('static', filename=current_user.profile_image) if current_user.profile_image else url_for('static', filename='assets/avatars/default-avatar.png') }}" 
                                 alt="Profile Image" 
                                 class="w-full h-full object-cover"
                                 onerror="this.src='{{ url_for('static', filename='assets/avatars/default-avatar.png') }}'">
                        </div>
                        
                        <!-- Upload Button Overlay -->
                        <button type="button" id="upload-btn" 
                                class="absolute bottom-0 right-0 bg-ki-green-600 text-white p-2 rounded-full shadow-lg hover:bg-ki-green-700 transition-colors">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                            </svg>
                        </button>
                    </div>
                    
                    <!-- Hidden File Input -->
                    <input type="file" id="profile-image-input" accept="image/*" class="hidden">
                    
                    <!-- Image Actions -->
                    <div class="flex justify-center space-x-2 mt-2">
                        <button type="button" id="select-avatar-btn" 
                                class="text-sm text-ki-green-600 hover:text-ki-green-700 font-medium">
                            Choose Avatar
                        </button>
                        <button type="button" id="remove-image-btn" 
                                class="text-sm text-red-600 hover:text-red-700 font-medium {% if not current_user.profile_image or current_user.profile_image.startswith('assets/avatars/') %}hidden{% endif %}">
                            Remove Custom Image
                        </button>
                    </div>
                </div>
                
                <p class="text-sm text-gray-500 mt-2">Click the + button to upload a custom image or "Choose Avatar" to select from predefined options</p>
            </div>
            
            <!-- Avatar Selection Modal -->
            <div id="avatar-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden z-50">
                <div class="flex items-center justify-center min-h-screen p-4">
                    <div class="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
                        <div class="p-6 border-b border-gray-200">
                            <div class="flex items-center justify-between">
                                <h3 class="text-lg font-semibold text-gray-900">Choose Your Avatar</h3>
                                <button type="button" id="close-avatar-modal" class="text-gray-400 hover:text-gray-600">
                                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                    </svg>
                                </button>
                            </div>
                        </div>
                        
                        <div class="p-6">
                            <div id="avatar-grid" class="grid grid-cols-3 md:grid-cols-4 gap-4">
                                <!-- Avatars will be loaded here -->
                            </div>
                        </div>
                    </div>
                </div>
            </div>'''

# Replace the profile image section
pattern = r'<!-- Profile Image Section -->.*?<p class="text-sm text-gray-500 mt-2">Click the \+ button to upload a profile image</p>\s*</div>'
content = re.sub(pattern, new_profile_section, content, flags=re.DOTALL)

# Write the updated content back
with open('templates/profile.html', 'w') as f:
    f.write(content)

print("Profile template updated with avatar selection!")
