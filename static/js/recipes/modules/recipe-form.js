/**
 * Recipe Form Module
 * Handles form validation, submission, and ingredient management
 */

// Prevent duplicate loading
if (typeof window.RecipeForm !== 'undefined') {
    // Already loaded, skip silently
} else {
    class RecipeForm {
    constructor(recipeManager) {
        this.recipeManager = recipeManager;
    }

    async createRecipe() {
        // Validate form before submission
        if (!this.validateRecipeForm()) {
            return;
        }

        const formData = new FormData();
        const imageFile = document.getElementById('recipe-image').files[0];
        
        // Add form data
        formData.append('name', document.getElementById('recipe-name').value.trim());
        formData.append('category', document.getElementById('recipe-category').value);
        formData.append('difficulty', document.getElementById('recipe-difficulty').value);
        formData.append('servings', document.getElementById('recipe-servings').value);
        formData.append('description', document.getElementById('recipe-description').value.trim());
        
        // Add prep and cook time
        const prepTime = document.getElementById('recipe-prep-time').value;
        const cookTime = document.getElementById('recipe-cook-time').value;
        if (prepTime) formData.append('prep_time', prepTime);
        if (cookTime) formData.append('cook_time', cookTime);
        
        // Add privacy setting
        const privacySetting = document.querySelector('input[name="is_public"]:checked');
        if (privacySetting) {
            formData.append('is_public', privacySetting.value === 'true');
        } else {
            formData.append('is_public', 'true'); // Default to community
        }
        
        // Process instructions - split by newlines and filter empty
        const instructionsText = document.getElementById('recipe-instructions').value.trim();
        const instructions = instructionsText.split('\n')
            .map(step => step.trim())
            .filter(step => step.length > 0);
        
        // Add instructions as individual steps
        instructions.forEach((instruction, index) => {
            formData.append(`instructions[${index}]`, instruction);
        });
        
        // Add image if selected
        if (imageFile) {
            formData.append('image', imageFile);
        }
        
        // Add ingredients with correct field names
        const ingredientsContainer = document.getElementById('ingredients-container');
        const ingredientRows = ingredientsContainer.querySelectorAll('.ingredient-row');
        
        ingredientRows.forEach((row, index) => {
            const name = row.querySelector('.ingredient-name').value.trim();
            const amount = row.querySelector('.ingredient-amount').value;
            const unit = row.querySelector('.ingredient-unit').value;
            
            if (name && amount && unit) {
                formData.append(`ingredients[${index}][food_name]`, name);
                formData.append(`ingredients[${index}][amount]`, amount);
                formData.append(`ingredients[${index}][unit]`, unit);
            }
        });
        
        try {
            const response = await fetch('/api/recipes', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.recipeManager.showToast('Recipe created successfully!', 'success');
                closeCreateModal();
                this.recipeManager.loadRecipes();
                this.resetCreateForm();
            } else {
                this.recipeManager.showToast(data.error || 'Failed to create recipe', 'error');
            }
        } catch (error) {
            console.error('Error creating recipe:', error);
            this.recipeManager.showToast('Failed to create recipe', 'error');
        }
    }

    validateRecipeForm() {
        // Check required fields
        const name = document.getElementById('recipe-name').value.trim();
        const category = document.getElementById('recipe-category').value;
        const difficulty = document.getElementById('recipe-difficulty').value;
        const servings = document.getElementById('recipe-servings').value;
        const instructions = document.getElementById('recipe-instructions').value.trim();
        
        if (!name) {
            this.recipeManager.showToast('Recipe name is required', 'error');
            document.getElementById('recipe-name').focus();
            return false;
        }
        
        if (!category) {
            this.recipeManager.showToast('Please select a category', 'error');
            document.getElementById('recipe-category').focus();
            return false;
        }
        
        if (!difficulty) {
            this.recipeManager.showToast('Please select a difficulty level', 'error');
            document.getElementById('recipe-difficulty').focus();
            return false;
        }
        
        if (!servings || servings < 1) {
            this.recipeManager.showToast('Please enter a valid number of servings', 'error');
            document.getElementById('recipe-servings').focus();
            return false;
        }
        
        if (!instructions) {
            this.recipeManager.showToast('Instructions are required', 'error');
            document.getElementById('recipe-instructions').focus();
            return false;
        }
        
        // Check ingredients
        const ingredientsContainer = document.getElementById('ingredients-container');
        const ingredientRows = ingredientsContainer.querySelectorAll('.ingredient-row');
        let validIngredients = 0;
        
        ingredientRows.forEach((row, index) => {
            const name = row.querySelector('.ingredient-name').value.trim();
            const amount = row.querySelector('.ingredient-amount').value;
            const unit = row.querySelector('.ingredient-unit').value;
            
            if (name && amount && unit) {
                validIngredients++;
            }
        });
        
        if (validIngredients === 0) {
            this.recipeManager.showToast('Please add at least one ingredient', 'error');
            return false;
        }
        
        // Check if image is uploaded (required for user-created recipes)
        const imageFile = document.getElementById('recipe-image').files[0];
        if (!imageFile) {
            this.recipeManager.showToast('Please select an image for your recipe. Images are required for all user-created recipes.', 'error');
            document.getElementById('recipe-image').focus();
            return false;
        }
        
        return true;
    }

    resetCreateForm() {
        document.getElementById('create-recipe-form').reset();
        document.getElementById('ingredients-container').innerHTML = '';
        document.getElementById('image-preview').classList.add('hidden');
        this.addIngredientRow(); // Add one default ingredient row
    }

    addIngredientRow() {
        const container = document.getElementById('ingredients-container');
        const rowCount = container.children.length;
        
        const row = document.createElement('div');
        row.className = 'ingredient-row flex space-x-2 items-center';
        row.innerHTML = `
            <input type="text" class="ingredient-name flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ki-green-500 focus:border-ki-green-500" placeholder="e.g., Chicken breast" required>
            <input type="number" class="ingredient-amount w-24 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ki-green-500 focus:border-ki-green-500" placeholder="1" min="0" step="0.1" required>
            <select class="ingredient-unit w-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ki-green-500 focus:border-ki-green-500" required>
                <option value="">Unit</option>
                <option value="g">grams</option>
                <option value="kg">kilograms</option>
                <option value="oz">ounces</option>
                <option value="lb">pounds</option>
                <option value="cup">cups</option>
                <option value="tbsp">tablespoons</option>
                <option value="tsp">teaspoons</option>
                <option value="whole">whole</option>
                <option value="slice">slices</option>
                <option value="piece">pieces</option>
            </select>
            ${rowCount > 0 ? `
                <button type="button" onclick="this.parentElement.remove()" class="px-3 py-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-lg transition-colors duration-200" title="Remove ingredient">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            ` : ''}
        `;
        
        container.appendChild(row);
    }

    handleImageUpload(file) {
        if (!file) return;
        
        if (!file.type.startsWith('image/')) {
            this.recipeManager.showToast('Please select an image file', 'error');
            return;
        }
        
        // Basic file size validation (removed 2MB limit since we'll transform the image)
        if (file.size < 1024) { // At least 1KB
            this.recipeManager.showToast('Image file is too small (min 1KB)', 'error');
            return;
        }
        
        // Check if file is very large and offer compression
        if (file.size > 20 * 1024 * 1024) { // 20MB
            this.recipeManager.showToast('Large image detected. Compressing for better upload performance...', 'info');
            this.compressAndUploadImage(file);
            return;
        }
        
        // Check for extremely large files
        if (file.size > 100 * 1024 * 1024) { // 100MB
            this.recipeManager.showToast('File too large (max 100MB). Please compress the image or use a smaller file.', 'error');
            return;
        }
        
        // Check filename for food-related keywords
        const filename = file.name.toLowerCase();
        const foodKeywords = [
            'food', 'meal', 'dish', 'recipe', 'cooking', 'kitchen', 'dinner', 'lunch', 'breakfast',
            'snack', 'dessert', 'soup', 'salad', 'pasta', 'pizza', 'burger', 'sandwich',
            'chicken', 'beef', 'fish', 'vegetable', 'fruit', 'bread', 'cake', 'cookie'
        ];
        
        const hasFoodKeyword = foodKeywords.some(keyword => filename.includes(keyword));
        
        // Check for non-food keywords that should be rejected
        const nonFoodKeywords = [
            'document', 'pdf', 'text', 'screenshot', 'photo', 'image', 'picture', 'selfie',
            'portrait', 'landscape', 'nature', 'animal', 'person', 'face', 'body',
            'logo', 'icon', 'banner', 'advertisement', 'ad', 'promo'
        ];
        
        const hasNonFoodKeyword = nonFoodKeywords.some(keyword => filename.includes(keyword));
        
        // If filename has non-food keywords but no food keywords, reject
        if (hasNonFoodKeyword && !hasFoodKeyword) {
            this.recipeManager.showToast('Please upload food-related images only. Use descriptive filenames like "chicken_recipe.jpg" or "healthy_salad.png"', 'error');
            return;
        }
        
        // Basic image dimension validation
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                // Check image dimensions
                if (img.width < 100 || img.height < 100) {
                    this.recipeManager.showToast('Image too small (min 100x100 pixels)', 'error');
                    return;
                }
                
                if (img.width > 8000 || img.height > 8000) {
                    this.recipeManager.showToast('Image too large (max 8000x8000 pixels). Please use a smaller image.', 'error');
                    return;
                }
                
                // Check aspect ratio
                const aspectRatio = img.width / img.height;
                if (aspectRatio > 5 || aspectRatio < 0.2) {
                    this.recipeManager.showToast('Please upload properly proportioned food images', 'error');
                    return;
                }
                
                // Show preview if validation passes
                const preview = document.getElementById('image-preview');
                const previewImg = document.getElementById('preview-img');
                previewImg.src = e.target.result;
                preview.classList.remove('hidden');
            };
            img.onerror = () => {
                this.recipeManager.showToast('Invalid image format', 'error');
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
    }

    removeImage() {
        document.getElementById('recipe-image').value = '';
        document.getElementById('image-preview').classList.add('hidden');
    }

    async compressAndUploadImage(file) {
        try {
            // Create a canvas to compress the image
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const img = new Image();
            
            return new Promise((resolve, reject) => {
                img.onload = () => {
                    // Calculate new dimensions (max 2000px on longest side)
                    let { width, height } = img;
                    const maxDimension = 2000;
                    
                    if (width > height && width > maxDimension) {
                        height = (height * maxDimension) / width;
                        width = maxDimension;
                    } else if (height > maxDimension) {
                        width = (width * maxDimension) / height;
                        height = maxDimension;
                    }
                    
                    // Set canvas dimensions
                    canvas.width = width;
                    canvas.height = height;
                    
                    // Draw and compress
                    ctx.drawImage(img, 0, 0, width, height);
                    
                    // Convert to blob with compression
                    canvas.toBlob((blob) => {
                        if (!blob) {
                            reject(new Error('Failed to compress image'));
                            return;
                        }
                        
                        // Create a new file from the compressed blob
                        const compressedFile = new File([blob], file.name, {
                            type: 'image/jpeg',
                            lastModified: Date.now()
                        });
                        
                        console.log(`Image compressed: ${file.size} -> ${compressedFile.size} bytes`);
                        
                        // Set the compressed file in the input field
                        const imageInput = document.getElementById('recipe-image');
                        if (imageInput) {
                            // Create a new FileList-like object
                            const dataTransfer = new DataTransfer();
                            dataTransfer.items.add(compressedFile);
                            imageInput.files = dataTransfer.files;
                            
                            // Show preview
                            const preview = document.getElementById('image-preview');
                            const previewImg = document.getElementById('preview-img');
                            previewImg.src = URL.createObjectURL(compressedFile);
                            preview.classList.remove('hidden');
                            
                            this.recipeManager.showToast('Image compressed and ready for upload!', 'success');
                        }
                        resolve(compressedFile);
                    }, 'image/jpeg', 0.8); // 80% quality
                };
                
                img.onerror = () => {
                    reject(new Error('Failed to load image for compression'));
                };
                
                img.src = URL.createObjectURL(file);
            });
        } catch (error) {
            console.error('Error compressing image:', error);
            this.recipeManager.showToast('Failed to compress image. Please try a smaller file.', 'error');
        }
    }
}

    // Export for use in other modules
    window.RecipeForm = RecipeForm;
}
