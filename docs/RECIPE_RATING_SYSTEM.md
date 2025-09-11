# Recipe Rating System Documentation

## Overview

The Ki Wellness application includes a comprehensive community recipe system with a rating architecture that allows users to share recipes and rate them. All recipes are community recipes by default, promoting sharing and collaboration.

## Architecture

### Database Schema

The `Recipe` model includes the following rating-related fields:

```python
class Recipe(db.Model):
    # ... existing fields ...
    average_rating = db.Column(db.Float, default=0.0)  # Average rating from all users
    rating_count = db.Column(db.Integer, default=0)    # Number of users who rated this recipe
    is_public = db.Column(db.Boolean, default=True)    # Always true for community recipes
```

### Rating Model

Individual ratings are stored in the `RecipeRating` model:

```python
class RecipeRating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    review = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

## Key Features

### 1. Community-First Approach
- All recipes are public by default
- No private recipes option in the creation modal
- Promotes sharing and community engagement

### 2. Rating System
- Users can rate recipes from 1-5 stars
- Average rating and count are stored in the Recipe model for performance
- Real-time updates when ratings are submitted
- Users can update their existing ratings

### 3. Permission System
- **Recipe Owners**: Can edit and delete their own recipes
- **All Users**: Can rate any public recipe
- **Contributor Display**: Shows the username of the recipe creator

### 4. Rating Display
- **Recipe Cards**: Show average rating with count format "4.2 (15)"
- **Recipe Modal**: Display stars + numeric value + count "(15 ratings)"
- **Consistent Formatting**: Same display format across all components

## API Endpoints

### Rate Recipe
```
POST /api/recipes/<int:recipe_id>/rate
```

**Request Body:**
```json
{
    "rating": 4,
    "review": "Great recipe!"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Recipe rated successfully",
    "average_rating": 4.2,
    "rating_count": 15
}
```

### Get Recipe Details
```
GET /api/recipes/<int:recipe_id>
```

**Response includes:**
```json
{
    "success": true,
    "recipe": {
        "id": 1,
        "name": "Recipe Name",
        "average_rating": 4.2,
        "rating_count": 15,
        "contributor": "username",
        "is_owner": false,
        "is_public": true,
        // ... other recipe fields
    }
}
```

## Database Methods

### Recipe.update_rating_stats()
Updates the stored average rating and count based on current ratings:

```python
def update_rating_stats(self):
    """Update average_rating and rating_count based on current ratings"""
    if self.ratings:
        total_rating = sum(r.rating for r in self.ratings)
        self.average_rating = round(total_rating / len(self.ratings), 1)
        self.rating_count = len(self.ratings)
    else:
        self.average_rating = 0.0
        self.rating_count = 0
```

## Frontend Implementation

### Recipe Cards
Display rating with count in the format "4.2 (15)":

```javascript
<div class="flex items-center space-x-1">
    <svg class="w-4 h-4 text-yellow-400" fill="currentColor">
        <!-- Star icon -->
    </svg>
    <span class="text-sm font-medium text-gray-700">${recipe.avg_rating || 0}</span>
    <span class="text-xs text-gray-500">(${recipe.rating_count || 0})</span>
</div>
```

### Recipe Modal
Show detailed rating information:

```javascript
<div class="flex items-center space-x-1">
    ${starsHtml}
    <span class="text-sm font-medium text-gray-700 ml-1">${rating}</span>
    <span class="text-sm text-gray-600 ml-1">(${ratingCount} ${ratingCount === 1 ? 'rating' : 'ratings'})</span>
</div>
```

### Rate Button
Conditionally shown for public recipes when user is not the owner:

```javascript
// Show/hide rate controls for public recipes
const rateControls = document.getElementById('modal-rate-controls');
if (rateControls) {
    if (recipe.is_public && !recipe.is_owner) {
        rateControls.classList.remove('hidden');
    } else {
        rateControls.classList.add('hidden');
    }
}
```

## Migration

The rating system was added via migration script `migrate_add_recipe_rating_fields.py`:

```python
# Add columns to Recipe table
ALTER TABLE recipe ADD COLUMN average_rating FLOAT DEFAULT 0.0;
ALTER TABLE recipe ADD COLUMN rating_count INTEGER DEFAULT 0;

# Update existing recipes with calculated ratings
for recipe in recipes:
    if recipe.ratings:
        total_rating = sum(r.rating for r in recipe.ratings)
        recipe.average_rating = round(total_rating / len(recipe.ratings), 1)
        recipe.rating_count = len(recipe.ratings)
    else:
        recipe.average_rating = 0.0
        recipe.rating_count = 0
```

## Best Practices

### Backend
1. Always use stored `average_rating` and `rating_count` fields for performance
2. Call `recipe.update_rating_stats()` after rating changes
3. Include `contributor` and `is_owner` fields in API responses
4. Validate rating values (1-5) on both frontend and backend
5. Check `recipe.is_public` before allowing rating operations

### Frontend
1. Use consistent rating display format across all components
2. Show rate button only for public recipes when user is not the owner
3. Update UI immediately after successful rating submission
4. Handle rating errors gracefully with user feedback

### Database
1. Index `recipe_id` and `user_id` in `RecipeRating` table for performance
2. Consider adding composite index on `(recipe_id, user_id)` for uniqueness
3. Regular cleanup of orphaned ratings if needed

## Testing

### Unit Tests
- Test rating creation and updates
- Test average calculation accuracy
- Test permission checks for rating operations

### Integration Tests
- Test complete rating flow from UI to database
- Test rating display across different components
- Test rating updates in real-time

### Performance Tests
- Test rating queries with large datasets
- Verify stored average calculation performance
- Test concurrent rating submissions

## Troubleshooting

### Common Issues

1. **Ratings not updating**: Check if `update_rating_stats()` is called after rating changes
2. **Duplicate ratings**: Ensure proper validation for existing user ratings
3. **Performance issues**: Verify database indexes are in place
4. **UI not updating**: Check if rating response includes updated stats

### Debug Commands

```python
# Check recipe rating stats
recipe = Recipe.query.get(recipe_id)
print(f"Average: {recipe.average_rating}, Count: {recipe.rating_count}")

# Verify individual ratings
ratings = RecipeRating.query.filter_by(recipe_id=recipe_id).all()
print(f"Individual ratings: {[r.rating for r in ratings]}")

# Recalculate ratings
recipe.update_rating_stats()
db.session.commit()
```

## Future Enhancements

### Potential Improvements
1. **Rating Analytics**: Track rating trends over time
2. **Rating Categories**: Different rating criteria (taste, difficulty, etc.)
3. **Rating Moderation**: Flag inappropriate ratings
4. **Rating Notifications**: Notify recipe owners of new ratings
5. **Rating Leaderboards**: Top-rated recipes and contributors

### Performance Optimizations
1. **Caching**: Cache rating stats for frequently accessed recipes
2. **Batch Updates**: Process multiple rating updates in batches
3. **Background Jobs**: Move rating calculations to background tasks
4. **Database Partitioning**: Partition rating tables by date or recipe

## Related Files

- `database.py` - Recipe and RecipeRating models
- `apis/recipe_api.py` - Rating API endpoints
- `templates/recipes/recipes.html` - Recipe UI components
- `static/js/recipes/modules/` - Frontend rating logic
- `migrations/migrate_add_recipe_rating_fields.py` - Database migration
