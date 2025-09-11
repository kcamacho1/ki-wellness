# Recipe Placeholder Images Guide

## Current Implementation

The recipe system now uses an intelligent placeholder image system that:

1. **First checks the recipe category** - Maps specific categories to appropriate images
2. **Analyzes ingredients** - Looks at the first few ingredients to determine the best image
3. **Falls back to default** - Uses a generic food image if no specific match is found

## Current Image Mappings

### Category-Based Images
- `breakfast` → `smoothie.jpg` (smoothies, bowls, breakfast items)
- `lunch` → `salad.jpg` (salads, light meals)
- `dinner` → `chicken.jpg` (main courses, proteins)
- `snack` → `smoothie.jpg` (healthy snacks)
- `dessert` → `soup.jpg` (temporary - needs better image)
- `soup` → `soup.jpg` (soups and stews)
- `salad` → `salad.jpg` (salads)
- `smoothie` → `smoothie.jpg` (smoothies and drinks)
- `pasta` → `pasta.jpg` (pasta dishes)
- `rice` → `rice.jpg` (rice dishes)
- `seafood` → `seafood.jpg` (fish and seafood)
- `vegetarian` → `veggies.jpg` (vegetarian dishes)
- `vegan` → `veggies.jpg` (vegan dishes)
- `keto` → `chicken.jpg` (keto-friendly meals)
- `paleo` → `chicken.jpg` (paleo meals)
- `gluten-free` → `rice.jpg` (gluten-free options)

### Ingredient-Based Images
The system analyzes ingredients and maps them to appropriate images:

**Protein Sources:**
- chicken → `chicken.jpg`
- beef, pork → `pork.jpg`
- turkey → `turkey.jpg`
- fish, salmon, tuna, shrimp, crab, lobster → `seafood.jpg`

**Grains & Carbs:**
- rice, quinoa, oats, bread → `rice.jpg`
- pasta, noodles → `pasta.jpg`

**Vegetables:**
- salad, lettuce, spinach, kale → `salad.jpg`
- vegetables, veggies, broccoli, carrots → `veggies.jpg`

**Soups & Liquids:**
- soup, broth → `soup.jpg`
- smoothie, juice → `smoothie.jpg`

## Recommended Image Sources

### Free Stock Photo Websites
1. **Unsplash** (https://unsplash.com)
   - High-quality, free images
   - Good food photography
   - No attribution required for most images

2. **Pexels** (https://pexels.com)
   - Free stock photos
   - Good food category
   - No attribution required

3. **Pixabay** (https://pixabay.com)
   - Free images and videos
   - Large food collection
   - Check individual image licenses

### Specific Search Terms for Better Images

**Breakfast:**
- "healthy breakfast bowl"
- "smoothie bowl"
- "avocado toast"
- "pancakes"
- "overnight oats"

**Lunch:**
- "fresh salad"
- "grain bowl"
- "sandwich"
- "soup bowl"

**Dinner:**
- "grilled chicken"
- "pasta dish"
- "stir fry"
- "roasted vegetables"

**Dessert:**
- "chocolate cake"
- "fruit tart"
- "ice cream"
- "cookies"

**Snacks:**
- "energy balls"
- "trail mix"
- "fruit"
- "nuts"

## Implementation Notes

### Current File Structure
```
static/assets/stock-photos/
├── chicken.jpg
├── pasta.jpg
├── pork.jpg
├── rice.jpg
├── salad.jpg
├── seafood.jpg
├── smoothie.jpg
├── soup.jpg
├── turkey.jpg
├── veggies.jpg
```

### Missing Images Needed
- `dessert.jpg` - Sweet treats, cakes, pies
- `breakfast.jpg` - Better breakfast image than smoothie
- `lunch.jpg` - Better lunch image than salad
- `snack.jpg` - Better snack image than smoothie

### Image Specifications
- **Format:** JPG or PNG
- **Size:** 400x300px minimum (4:3 aspect ratio)
- **Quality:** High resolution, well-lit, appetizing
- **Style:** Consistent lighting and color palette
- **Content:** Clear, appetizing food photography

## Future Enhancements

### Dynamic Image Loading
Consider implementing a dynamic image loading system using APIs:

```javascript
async function fetchPlaceholderImage(recipe) {
    const query = generateImageQuery(recipe);
    const apiKey = 'YOUR_UNSPLASH_API_KEY';
    const url = `https://api.unsplash.com/search/photos?query=${query}&client_id=${apiKey}`;
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        return data.results[0]?.urls.small || getDefaultImage(recipe);
    } catch (error) {
        return getDefaultImage(recipe);
    }
}
```

### Caching System
Implement local caching to avoid repeated API calls:
- Store fetched images locally
- Use localStorage or IndexedDB
- Set appropriate cache expiration

### Fallback Chain
1. Recipe's own image
2. Smart category/ingredient-based image
3. Generic category image
4. Default fallback image

## Usage

The system automatically selects the best placeholder image when:
- A recipe has no image (`image_path` is null/empty)
- A recipe's image fails to load (onerror event)
- Displaying recipes in the grid or modal

No manual intervention is required - the system intelligently chooses the most appropriate image based on the recipe's category and ingredients.
