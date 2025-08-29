# AI-related routes
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from database import db, FoodLog, WaterLog, MoodLog, Note, User, AIAnalysis
from services.openrouter_client import get_openrouter_client
from services.analytics_service import analytics_service
from utils.decorators import premium_required
from security_middleware import rate_limit
from utils.helpers import (
    validate_user_input, 
    sanitize_user_input, 
    check_ai_usage_limits,
    OPENROUTER_MODEL
)

# Create blueprint
ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/api/generate-ai-analysis', methods=['POST'])
@login_required
@premium_required
def generate_ai_analysis():
    """Generate AI-powered health analysis using OpenRouter"""
    try:
        # Get user profile data from current_user
        profile = {
            'name': current_user.name,
            'age': current_user.age,
            'weight': current_user.weight,
            'height': current_user.height,
            'health_goals': current_user.health_goals,
            'ailments_concerns': current_user.ailments_concerns
        }
        
        # Get last 7 days of data for weekly analysis
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        # Get food logs
        food_logs = FoodLog.query.filter(
            FoodLog.user_id == current_user.id,
            FoodLog.date >= start_date,
            FoodLog.date <= end_date
        ).all()
        
        # Get water logs
        water_logs = WaterLog.query.filter(
            WaterLog.user_id == current_user.id,
            WaterLog.date >= start_date,
            WaterLog.date <= end_date
        ).all()
        
        # Get mood logs
        mood_logs = MoodLog.query.filter(
            MoodLog.user_id == current_user.id,
            MoodLog.date >= start_date,
            MoodLog.date <= end_date
        ).all()
        
        # Get notes
        notes = Note.query.filter(
            Note.user_id == current_user.id,
            Note.date >= start_date,
            Note.date <= end_date
        ).all()
        
        # Convert to dicts for processing
        food_logs = [{
            'name': log.name,
            'calories': log.calories,
            'protein': log.protein,
            'carbs': log.carbs,
            'fat': log.fat,
            'time_of_day': log.time_of_day,
            'date': log.date.isoformat()
        } for log in food_logs]
        
        water_logs = [{
            'amount': log.amount,
            'date': log.date.isoformat()
        } for log in water_logs]
        
        mood_logs = [{
            'mood': log.mood,
            'date': log.date.isoformat()
        } for log in mood_logs]
        
        notes = [{
            'content': log.content,
            'date': log.date.isoformat()
        } for log in notes]
        
        # Calculate basic statistics
        avg_calories = sum(log.get('calories', 0) for log in food_logs) / len(food_logs) if food_logs else 0
        total_water = sum(log.get('amount', 0) for log in water_logs)
        avg_water = total_water / len(water_logs) if water_logs else 0
        avg_mood = sum(log.get('mood', 3) for log in mood_logs) / len(mood_logs) if mood_logs else 3
        
        # Group food by time of day and get top foods
        food_by_time = {}
        for log in food_logs:
            time_of_day = log.get('time_of_day', 'snack')
            if time_of_day not in food_by_time:
                food_by_time[time_of_day] = []
            food_by_time[time_of_day].append(log)
        
        # Get most recent and frequent foods (limit to prevent token overflow)
        recent_foods = food_logs[-3:] if len(food_logs) > 3 else food_logs
        recent_notes = notes[-2:] if len(notes) > 2 else notes
        
        # Build recent activity strings safely to avoid deep f-string nesting
        recent_foods_list = [f"{log.get('name', 'Unknown')} ({log.get('time_of_day', 'snack')})" for log in recent_foods]
        recent_moods_list = [log.get('mood') for log in mood_logs[-2:]]
        recent_notes_list = [
            (note.get('content', '')[:80] + '...') if len(note.get('content', '') or '') > 80 else (note.get('content', '') or '')
            for note in recent_notes
        ]

        analysis_template = (
            """
        Weekly Health Coach Analysis - concise, evidence-based, grounded in local knowledge.

        USER: {user_name} | Age: {user_age} | Goals: {user_goals} | Health Concerns: {user_ailments}

        DATA SUMMARY (past 7 days):
        - Food: {food_count} entries, ~{avg_cal:.0f} kcal/day
        - Water: {water_count} entries, ~{avg_water:.1f} cups/day
        - Mood: {mood_count} entries, ~{avg_mood:.1f}/5
        - Notes: {notes_count} entries

        RECENT ACTIVITY:
        - Food (most recent): {recent_foods}
        - Mood (most recent): {recent_moods}
        - Notes (snippets): {recent_notes}

        TASK:
        - Analyze patterns from the past 7 days connecting mood & notes to food & water intake (e.g., low water -> lower mood next day, high sugar late at night -> poorer mood).
        - Provide short explanations for likely reasons behind how the user is feeling based on these weekly patterns.
        - Create 2-3 actionable, personalized suggestions to try this upcoming week.
        - Ground suggestions in nutrition science and behavior change research. Include brief source citations when helpful.

        OUTPUT STRICT JSON ONLY:
        {{
          "patterns": [
            {{"title": "Pattern Title", "description": "Brief description of the weekly data-backed pattern (mood vs. notes, food, water)."}}
          ],
          "suggestions": [
            {{
              "title": "Suggestion Title",
              "description": "Brief, actionable advice for the upcoming week based on patterns.",
              "sources": [
                {{"title": "Short Source Name", "url": "https://example.com"}}
              ]
            }}
          ]
        }}
        """
        )

        analysis_prompt = analysis_template.format(
            user_name=profile.get('name', 'User'),
            user_age=profile.get('age', 'N/A'),
            user_goals=profile.get('health_goals', 'Not specified'),
            user_ailments=profile.get('ailments_concerns', 'Not specified'),
            food_count=len(food_logs),
            avg_cal=avg_calories,
            water_count=len(water_logs),
            avg_water=avg_water,
            mood_count=len(mood_logs),
            avg_mood=avg_mood,
            notes_count=len(notes),
            recent_foods=json.dumps(recent_foods_list),
            recent_moods=json.dumps(recent_moods_list),
            recent_notes=json.dumps(recent_notes_list),
        )
        
        # Use OpenRouter for AI analysis
        try:
            client = get_openrouter_client()
            ai_response = client.generate_response(
                prompt=analysis_prompt,
                model=OPENROUTER_MODEL,
                max_tokens=800
            )
        except Exception as e:
            print(f"OpenRouter error: {e}")
            # Fallback response
            ai_response = json.dumps({
                "patterns": [
                    {"title": "Data Analysis", "description": "We're analyzing your wellness patterns. Keep logging to get more personalized insights!"}
                ],
                "suggestions": [
                    {"title": "Complete Your Profile", "description": "Add your health goals to your profile to get personalized suggestions."}
                ]
            })
        
        # Parse the JSON response
        try:
            analysis = json.loads(ai_response)
        except json.JSONDecodeError:
            # If JSON parsing fails, create a fallback response
            analysis = {
                "patterns": [
                    {"title": "Data Analysis", "description": "We're analyzing your wellness patterns. Keep logging to get more personalized insights!"}
                ],
                "suggestions": [
                    {"title": "Complete Your Profile", "description": "Add your health goals to your profile to get personalized suggestions."}
                ]
            }
        
        # Save analysis to database
        try:
            # Check if user already has an analysis record
            existing_analysis = AIAnalysis.query.filter_by(user_id=current_user.id).first()
            
            if existing_analysis:
                # Update existing analysis
                existing_analysis.analysis_data = json.dumps(analysis)
                existing_analysis.updated_at = datetime.utcnow()
            else:
                # Create new analysis record
                new_analysis = AIAnalysis(
                    user_id=current_user.id,
                    analysis_data=json.dumps(analysis)
                )
                db.session.add(new_analysis)
            
            db.session.commit()
            print(f"✅ AI analysis saved for user {current_user.id}")
            
        except Exception as save_error:
            print(f"❌ Error saving analysis to database: {save_error}")
            # Continue even if save fails - analysis is still returned to user
        
        return jsonify({'success': True, 'analysis': analysis})
        
    except Exception as e:
        print(f"AI Analysis Error: {str(e)}")  # Add debugging
        return jsonify({'success': False, 'error': str(e)})

def enhanced_ai_response(question: str, user_data: dict = None) -> str:
    """Generate enhanced AI response using OpenRouter API"""
    try:
        # Check if user has premium access (this function is called from other contexts)
        if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
            if not current_user.has_premium_access():
                return "This feature requires a premium subscription. Upgrade now to access AI-powered wellness insights!"
        
        client = get_openrouter_client()
        return client.generate_response(
            prompt=question,
            model=OPENROUTER_MODEL,
            max_tokens=500
        )
    except Exception as e:
        print(f"❌ Error generating enhanced response: {e}")
        return "I apologize, but I encountered an error while processing your request."

@ai_bp.route('/api/test-openrouter')
@login_required
def test_openrouter():
    try:
        client = get_openrouter_client()
        response = client.generate_response(
            prompt="Say 'Hello, AI is working!'",
            model=OPENROUTER_MODEL
        )
        
        return jsonify({'success': True, 'response': response})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@ai_bp.route('/api/warmup-openrouter')
@login_required
def warmup_openrouter():
    """Test OpenRouter API connection"""
    try:
        # Simple test call
        client = get_openrouter_client()
        response = client.generate_response(
            prompt="Hello",
            model=OPENROUTER_MODEL,
            max_tokens=10
        )
        return jsonify({'success': True, 'message': 'OpenRouter API is working', 'response': response})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@ai_bp.route('/api/user-summary')
@login_required
def get_user_summary():
    """Get summarized user data for AI chat (last 7 days)"""
    try:
        from datetime import timedelta
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        # Get user profile
        user_profile = {
            'id': current_user.id,
            'name': current_user.name,
            'age': current_user.age,
            'weight': current_user.weight,
            'height': current_user.height,
            'health_goals': current_user.health_goals,
            'ailments_concerns': current_user.ailments_concerns
        }
        
        # Get summarized food data
        food_logs = FoodLog.query.filter(
            FoodLog.user_id == current_user.id,
            FoodLog.date >= start_date,
            FoodLog.date <= end_date
        ).all()
        
        food_summary = {
            'total_entries': len(food_logs),
            'avg_calories': sum(log.calories for log in food_logs) / len(food_logs) if food_logs else 0,
            'total_calories': sum(log.calories for log in food_logs),
            'common_foods': _get_common_foods(food_logs),
            'recent_meals': [{
                'name': log.name,
                'calories': log.calories,
                'date': log.date.isoformat(),
                'time_of_day': log.time_of_day
            } for log in food_logs[-5:]]  # Last 5 meals
        }
        
        # Get summarized mood data
        mood_logs = MoodLog.query.filter(
            MoodLog.user_id == current_user.id,
            MoodLog.date >= start_date,
            MoodLog.date <= end_date
        ).all()
        
        mood_summary = {
            'total_entries': len(mood_logs),
            'avg_mood': sum(log.mood for log in mood_logs) / len(mood_logs) if mood_logs else 0,
            'mood_trend': _get_mood_trend(mood_logs),
            'recent_moods': [{
                'mood': log.mood,
                'date': log.date.isoformat()
            } for log in mood_logs[-5:]]
        }
        
        # Get summarized water data
        water_logs = WaterLog.query.filter(
            WaterLog.user_id == current_user.id,
            WaterLog.date >= start_date,
            WaterLog.date <= end_date
        ).all()
        
        water_summary = {
            'total_entries': len(water_logs),
            'total_water': sum(log.amount for log in water_logs),
            'avg_daily_water': sum(log.amount for log in water_logs) / 7 if water_logs else 0,
            'recent_water': [{
                'amount': log.amount,
                'date': log.date.isoformat()
            } for log in water_logs[-5:]]
        }
        
        # Get recent patterns from stored analysis
        recent_patterns = []
        analysis_record = AIAnalysis.query.filter_by(user_id=current_user.id).first()
        if analysis_record:
            analysis_data = json.loads(analysis_record.analysis_data)
            recent_patterns = analysis_data.get('patterns', [])[:3]  # Top 3 patterns
        
        return jsonify({
            'success': True,
            'summary': {
                'profile': user_profile,
                'food_summary': food_summary,
                'mood_summary': mood_summary,
                'water_summary': water_summary,
                'recent_patterns': recent_patterns
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@ai_bp.route('/api/ai-chat', methods=['POST'])
@premium_required
@rate_limit(max_requests=30, window=60)  # Limit AI chat requests
def ai_chat():
    try:
        # Check AI usage limits before processing request
        limits_ok, limit_message = check_ai_usage_limits(current_user.id)
        if not limits_ok:
            return jsonify({
                'success': False, 
                'error': f'AI usage limit exceeded: {limit_message}',
                'limit_exceeded': True
            }), 429  # Too Many Requests
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request data'}), 400
            
        message = data.get('message', '').strip()
        context = data.get('context', {})
        context_type = data.get('context_type', 'minimal')
        chat_history = data.get('chat_history', [])
        
        # Input validation and sanitization
        if not validate_user_input(message, max_length=1000):
            return jsonify({'success': False, 'error': 'Invalid message format'}), 400
            
        if not validate_user_input(context_type, max_length=50):
            return jsonify({'success': False, 'error': 'Invalid context type'}), 400
            
        # Validate chat history structure separately (list of dict objects with role/content)
        if chat_history is not None:
            if not isinstance(chat_history, list):
                return jsonify({'success': False, 'error': 'Invalid chat history format - must be a list'}), 400
            
            # Limit the number of history items and validate each
            if len(chat_history) > 10:  # Reasonable limit for chat history
                return jsonify({'success': False, 'error': 'Too many chat history items'}), 400
                
            for i, item in enumerate(chat_history):
                if not isinstance(item, dict):
                    return jsonify({'success': False, 'error': f'Invalid chat history item {i} - must be a dict'}), 400
                
                role = item.get('role', '')
                content = item.get('content', '')
                
                if role not in ['user', 'assistant']:
                    return jsonify({'success': False, 'error': f'Invalid chat history role in item {i}'}), 400
                    
                if not validate_user_input(content, max_length=2000):  # Allow longer content for chat history
                    return jsonify({'success': False, 'error': f'Invalid chat history content in item {i}'}), 400
        
        # Sanitize inputs
        message = sanitize_user_input(message, max_length=1000)
        context_type = sanitize_user_input(context_type, max_length=50)
        
        # Sanitize chat history content while preserving structure
        if chat_history:
            for item in chat_history:
                if isinstance(item, dict) and 'content' in item:
                    item['content'] = sanitize_user_input(item['content'], max_length=2000)
        
        print(f"AI Chat Request - Message: {message}")
        print(f"AI Chat Request - Context Type: {context_type}")
        print(f"AI Chat Request - Context Keys: {list(context.keys()) if context else 'None'}")
        
        if not message:
            return jsonify({'success': False, 'error': 'No message provided'})
        
        # Create optimized prompt based on context type
        try:
            prompt = _create_optimized_prompt(message, context, context_type, chat_history)
            print(f"AI Chat - Prompt length: {len(prompt)} characters")
        except Exception as prompt_error:
            print(f"AI Chat - Prompt creation error: {str(prompt_error)}")
            return jsonify({'success': False, 'error': f'Prompt creation failed: {str(prompt_error)}'})
        
        # Call OpenRouter API with timeout
        try:
            start_time = datetime.now()
            client = get_openrouter_client()
            ai_response = client.generate_response(
                prompt=prompt,
                model=OPENROUTER_MODEL,
                max_tokens=500
            )
            
            response_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            print(f"AI Chat - Response received, length: {len(ai_response)} characters")
            
            # Log AI usage for analytics (if we have usage data)
            try:
                # Estimate token counts (OpenRouter doesn't always return usage info)
                estimated_input_tokens = len(prompt.split()) * 1.3  # Rough estimate
                estimated_output_tokens = len(ai_response.split()) * 1.3
                
                # Get model pricing for cost calculation
                model_pricing = client.get_model_pricing(OPENROUTER_MODEL)
                input_cost = (estimated_input_tokens / 1000000) * model_pricing.get('input', 0.20)
                output_cost = (estimated_output_tokens / 1000000) * model_pricing.get('output', 0.80)
                
                # Safety check: ensure costs are finite values
                if not (isinstance(input_cost, (int, float)) and input_cost != float('inf') and input_cost != float('-inf')):
                    input_cost = 0.0
                if not (isinstance(output_cost, (int, float)) and output_cost != float('inf') and output_cost != float('-inf')):
                    output_cost = 0.0
                
                analytics_service.log_ai_usage(
                    user_id=current_user.id,
                    model_used=OPENROUTER_MODEL,
                    input_tokens=int(estimated_input_tokens),
                    output_tokens=int(estimated_output_tokens),
                    input_cost=input_cost,
                    output_cost=output_cost,
                    endpoint='/api/ai-chat',
                    response_time_ms=response_time_ms,
                    success=True
                )
            except Exception as log_error:
                print(f"⚠️ Could not log AI usage: {log_error}")
            
            return jsonify({'success': True, 'response': ai_response})
            
        except Exception as openrouter_error:
            print(f"AI Chat - OpenRouter error: {str(openrouter_error)}")
            
            # Log failed usage attempt
            try:
                analytics_service.log_ai_usage(
                    user_id=current_user.id,
                    model_used=OPENROUTER_MODEL,
                    input_tokens=len(prompt.split()),
                    output_tokens=0,
                    input_cost=0,
                    output_cost=0,
                    endpoint='/api/ai-chat',
                    response_time_ms=0,
                    success=False,
                    error_message=str(openrouter_error)
                )
            except Exception as log_error:
                print(f"⚠️ Could not log failed AI usage: {log_error}")
            
            # Provide a helpful fallback response when OpenRouter is not available
            fallback_response = _get_fallback_response(message, context_type)
            return jsonify({
                'success': True, 
                'response': fallback_response,
                'note': 'Using fallback response - AI model temporarily unavailable'
            })
        
    except Exception as e:
        print(f"AI Chat - General error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def _create_optimized_prompt(message, context, context_type, chat_history):
    """Create an optimized prompt based on context type"""
    
    # Safely get context values with error handling
    try:
        profile = context.get('profile', {}) if context else {}
        profile_name = profile.get('name', 'User') if profile else 'User'
    except Exception as e:
        print(f"Error extracting profile data: {e}")
        profile_name = 'User'
    
    # Start with a concise base prompt
    base_prompt = f"AI Health Coach for {profile_name}. Keep responses short and actionable. When referring to the user, use their name '{profile_name}' instead of 'the user' or 'you'.\n\nQ: {message}\n\n"
    
    # Add only essential context based on the specific question
    relevant_context = _extract_relevant_context(message, context, context_type)
    if relevant_context and len(relevant_context) < 100:  # Only add if context is concise
        base_prompt += f"Context: {relevant_context}\n"
        print(f"Extracted relevant context: {relevant_context}")
    
    base_prompt += f"""Provide a short, helpful response (max 2-3 sentences). When referring to the user, use their name '{profile_name}' instead of generic terms. You may include relevant links naturally in your response text when helpful, especially to the company's Medium blog (kiwellness.medium.com) when relevant. Do not include a separate resources section."""
    
    # Proactive prompt size management
    if len(base_prompt) > 800:  # Lower threshold for better optimization
        print(f"Prompt too large ({len(base_prompt)} chars), optimizing...")
        # Create ultra-concise version
        base_prompt = f"AI Health Coach for {profile_name}. Q: {message}\n\nProvide short, helpful response. Use '{profile_name}' when referring to the user, not 'the user'. You may include relevant links naturally when helpful, especially the company's Medium blog when relevant."
    
    print(f"Final prompt length: {len(base_prompt)} characters")
    return base_prompt

def _determine_topic(message):
    """Determine the specific topic of the user's question for resource matching"""
    
    message_lower = message.lower()
    
    # Nutrition topics
    if any(word in message_lower for word in ['energy', 'energizing', 'boost', 'power', 'fuel']):
        return 'nutrition'
    elif any(word in message_lower for word in ['calorie', 'calories', 'weight', 'diet', 'meal', 'eating', 'food']):
        return 'nutrition'
    
    # Mood topics
    elif any(word in message_lower for word in ['mood', 'feel', 'emotion', 'happy', 'sad', 'stress', 'anxiety', 'depression']):
        return 'mood'
    
    # Hydration topics
    elif any(word in message_lower for word in ['water', 'hydrate', 'drink', 'fluid', 'dehydrated']):
        return 'hydration'
    
    # Exercise topics
    elif any(word in message_lower for word in ['exercise', 'workout', 'fitness', 'activity', 'training']):
        return 'exercise'
    
    # General wellness
    elif any(word in message_lower for word in ['health', 'wellness', 'habit', 'lifestyle', 'goal']):
        return 'wellness'
    
    # Default to general
    return 'general'

def _get_fallback_response(message, context_type):
    """Provide helpful fallback responses when AI model is unavailable"""
    
    message_lower = message.lower()
    
    # Anti-inflammation responses
    if any(word in message_lower for word in ['anti-inflammation', 'anti-inflammatory', 'inflammation']):
        return """For anti-inflammatory meals, focus on foods rich in omega-3s, antioxidants, and fiber. Try a salmon salad with leafy greens, berries, and walnuts, or a turmeric-spiced lentil soup with ginger.

📚 Helpful Resources:
- [Anti-Inflammatory Diet Guide](https://kiwellness.medium.com/anti-inflammatory-foods) - Ki Wellness blog
- [Mayo Clinic: Anti-inflammatory diet](https://www.mayoclinic.org/healthy-lifestyle/nutrition-and-healthy-eating/in-depth/anti-inflammatory-diet/art-20457586) - Medical guidance"""
    
    # Energy and nutrition
    elif any(word in message_lower for word in ['energy', 'energizing', 'boost', 'meal', 'food', 'nutrition']):
        return """For sustained energy, combine complex carbs with protein and healthy fats. Try oatmeal with nuts and berries, or a quinoa bowl with vegetables and lean protein.

📚 Helpful Resources:
- [Energy-Boosting Foods](https://kiwellness.medium.com/energy-foods) - Ki Wellness blog
- [Harvard Health: Foods that fight fatigue](https://www.health.harvard.edu/healthbeat/foods-that-fight-fatigue) - Expert advice"""
    
    # Water and hydration
    elif any(word in message_lower for word in ['water', 'hydrate', 'drink']):
        return """Stay hydrated by drinking water throughout the day. Aim for 8-10 glasses daily, and include hydrating foods like cucumbers, watermelon, and citrus fruits.

📚 Helpful Resources:
- [Hydration Tips](https://kiwellness.medium.com/hydration-guide) - Ki Wellness blog
- [WebMD: How much water should you drink?](https://www.webmd.com/diet/how-much-water-to-drink) - Daily recommendations"""
    
    # Mood and wellness
    elif any(word in message_lower for word in ['mood', 'feel', 'stress', 'anxiety', 'wellness']):
        return """Support your mood with regular exercise, adequate sleep, and mood-boosting foods like dark chocolate, fatty fish, and leafy greens. Practice stress management techniques daily.

📚 Helpful Resources:
- [Mood-Boosting Habits](https://kiwellness.medium.com/mood-wellness) - Ki Wellness blog
- [Mayo Clinic: Stress management](https://www.mayoclinic.org/healthy-lifestyle/stress-management) - Expert guidance"""
    
    # General health
    else:
        return """I'm here to support your wellness journey! For personalized guidance, try logging your meals, water intake, and mood regularly. This helps identify patterns and make informed health decisions.

📚 Helpful Resources:
- [Wellness Tips](https://kiwellness.medium.com/wellness-guide) - Ki Wellness blog
- [Personalized Health Coaching](https://kiwellness.org/human-help) - Book a session with our certified nutritionist"""

def _extract_relevant_context(message, context, context_type):
    """Extract only context that's relevant to the user's specific question"""
    
    message_lower = message.lower()
    relevant_parts = []
    
    try:
        # Food-related questions
        if context_type == 'food' and context.get('food_summary'):
            food_data = context['food_summary']
            
            # Check for specific food-related keywords
            if any(word in message_lower for word in ['energy', 'energizing', 'boost', 'power']):
                # For energy questions, focus on calorie intake and meal frequency
                relevant_parts.append(f"Logged {food_data.get('total_entries', 0)} meals")
                if food_data.get('avg_calories', 0) > 0:
                    relevant_parts.append(f"avg {food_data.get('avg_calories', 0):.0f} cal/meal")
                    
            elif any(word in message_lower for word in ['calorie', 'calories', 'weight', 'diet']):
                # For calorie/weight questions, focus on total calories
                total_cals = food_data.get('total_calories', 0)
                relevant_parts.append(f"Total calories: {total_cals:.0f}")
                if food_data.get('avg_calories', 0) > 0:
                    relevant_parts.append(f"avg {food_data.get('avg_calories', 0):.0f} cal/meal")
                    
            elif any(word in message_lower for word in ['meal', 'eating', 'food', 'nutrition']):
                # For general food questions, provide basic summary
                relevant_parts.append(f"Logged {food_data.get('total_entries', 0)} meals")
                if food_data.get('common_foods'):
                    common_foods = food_data.get('common_foods', [])[:3]
                    relevant_parts.append(f"common foods: {', '.join(common_foods)}")
                    
            else:
                # Default food context - keep it concise
                relevant_parts.append(f"Logged {food_data.get('total_entries', 0)} meals")
                if food_data.get('avg_calories', 0) > 0:
                    relevant_parts.append(f"avg {food_data.get('avg_calories', 0):.0f} cal/meal")
        
        # Mood-related questions
        elif context_type == 'mood' and context.get('mood_summary'):
            mood_data = context['mood_summary']
            
            if any(word in message_lower for word in ['trend', 'pattern', 'improving', 'declining']):
                # For trend questions, focus on mood trend
                relevant_parts.append(f"Mood trend: {mood_data.get('mood_trend', 'stable')}")
                if mood_data.get('avg_mood', 0) > 0:
                    relevant_parts.append(f"avg {mood_data.get('avg_mood', 0):.1f}/10")
                    
            elif any(word in message_lower for word in ['happy', 'sad', 'stress', 'anxiety', 'depression']):
                # For emotional state questions, focus on current mood
                if mood_data.get('avg_mood', 0) > 0:
                    relevant_parts.append(f"Current avg mood: {mood_data.get('avg_mood', 0):.1f}/10")
                if mood_data.get('mood_trend', 'stable') != 'stable':
                    relevant_parts.append(f"trend: {mood_data.get('mood_trend', 'stable')}")
            else:
                # Default mood context
                if mood_data.get('avg_mood', 0) > 0:
                    relevant_parts.append(f"Avg mood: {mood_data.get('avg_mood', 0):.1f}/10")
        
        # Water-related questions
        elif context_type == 'water' and context.get('water_summary'):
            water_data = context['water_summary']
            
            if any(word in message_lower for word in ['enough', 'adequate', 'sufficient', 'dehydrated']):
                # For hydration adequacy questions, compare to recommended intake
                avg_daily = water_data.get('avg_daily_water', 0)
                relevant_parts.append(f"Daily avg: {avg_daily:.0f}ml")
                if avg_daily < 2000:
                    relevant_parts.append("(below 2000ml)")
                elif avg_daily > 3000:
                    relevant_parts.append("(above 3000ml)")
                    
            elif any(word in message_lower for word in ['increase', 'more', 'boost']):
                # For increasing water intake
                current_avg = water_data.get('avg_daily_water', 0)
                relevant_parts.append(f"Daily avg: {current_avg:.0f}ml")
                
            else:
                # Default water context - keep concise
                relevant_parts.append(f"Daily avg: {water_data.get('avg_daily_water', 0):.0f}ml")
        
        # Analysis/pattern questions
        elif context_type == 'analysis' and context.get('recent_patterns'):
            recent_patterns = context.get('recent_patterns', [])
            
            if any(word in message_lower for word in ['pattern', 'trend', 'insight', 'analysis']):
                if recent_patterns:
                    # Extract key insights from patterns
                    pattern_titles = [p.get('title', '') for p in recent_patterns[:2]]
                    relevant_parts.append(f"Key patterns: {', '.join(pattern_titles)}")
                else:
                    relevant_parts.append("No recent patterns identified")
        
        # Health goals context (for any question)
        if context.get('profile', {}).get('health_goals'):
            goals = context['profile']['health_goals']
            if any(word in message_lower for word in ['goal', 'target', 'objective', 'aim']):
                relevant_parts.append(f"Health goals: {goals}")
        
        # Ailments/concerns context (for health-related questions)
        if context.get('profile', {}).get('ailments_concerns'):
            ailments = context['profile']['ailments_concerns']
            # More specific keywords to avoid conflicts with health goals
            if any(word in message_lower for word in ['condition', 'ailment', 'concern', 'medical', 'symptom', 'issue', 'diabetes', 'blood pressure', 'pressure', 'disease', 'chronic', 'manage', 'management', 'avoid', 'safe', 'affect']):
                relevant_parts.append(f"Health concerns: {ailments}")
        
        # Age context (for age-specific advice)
        if context.get('profile', {}).get('age'):
            age = context['profile']['age']
            if any(word in message_lower for word in ['age', 'older', 'younger', 'senior', 'teen']):
                relevant_parts.append(f"Age: {age}")
        
    except Exception as e:
        print(f"Error extracting relevant context: {e}")
        return None
    
    return '; '.join(relevant_parts) if relevant_parts else None

def _get_common_foods(food_logs):
    """Get most common foods from logs"""
    food_counts = {}
    for log in food_logs:
        food_name = log.name.lower()
        food_counts[food_name] = food_counts.get(food_name, 0) + 1
    
    return [food for food, count in sorted(food_counts.items(), key=lambda x: x[1], reverse=True)[:5]]

def _get_mood_trend(mood_logs):
    """Determine mood trend from recent logs"""
    if len(mood_logs) < 2:
        return 'insufficient_data'
    
    recent_moods = [log.mood for log in mood_logs[-3:]]
    if len(recent_moods) >= 2:
        if recent_moods[-1] > recent_moods[0]:
            return 'improving'
        elif recent_moods[-1] < recent_moods[0]:
            return 'declining'
        else:
            return 'stable'
    return 'stable'
