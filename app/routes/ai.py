"""
Ki Wellness - AI Routes
=======================

This module contains AI-related routes for chat functionality
and AI-powered wellness analysis.

Author: Ki Wellness Team
Version: 2.0
"""

from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
from ..models import db, AIUsageSession
from ..services import UserService, AIService
from ..decorators import login_required

# Create blueprint
ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/ai/chat', methods=['POST'])
@login_required
def ai_chat():
    """Handle AI chat requests"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Check if user can use AI
        if not UserService.can_user_use_ai(current_user.id):
            return jsonify({'success': False, 'error': 'AI features not available'}), 403
        
        # Create AI usage session
        session = AIUsageSession(
            user_id=current_user.id,
            session_type='chat',
            input_tokens=len(message.split()),  # Rough estimate
            output_tokens=0,  # Will be updated after response
            cost_usd=0.0,  # Will be calculated after response
            status='in_progress'
        )
        
        db.session.add(session)
        db.session.commit()
        
        # Get AI response
        result = AIService.get_ai_chat_response(current_user.id, message, session.id)
        
        if result['success']:
            # Update session with actual usage
            session.output_tokens = result.get('output_tokens', 0)
            session.cost_usd = result.get('cost_usd', 0.0)
            session.status = 'completed'
            session.completed_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'response': result.get('response', ''),
                'tokens_used': session.input_tokens + session.output_tokens,
                'cost_usd': session.cost_usd
            })
        else:
            # Update session as failed
            session.status = 'failed'
            session.error_message = result.get('error', 'Unknown error')
            session.completed_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({'success': False, 'error': result.get('error', 'Failed to get AI response')}), 500
        
    except Exception as e:
        print(f"❌ Error in AI chat: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@ai_bp.route('/ai/analysis', methods=['POST'])
@login_required
def ai_analysis():
    """Handle AI wellness analysis requests"""
    try:
        data = request.get_json()
        analysis_type = data.get('type', 'general')
        context = data.get('context', '')
        
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Check if user can use AI
        if not UserService.can_user_use_ai(current_user.id):
            return jsonify({'success': False, 'error': 'AI features not available'}), 403
        
        # Create AI usage session
        session = AIUsageSession(
            user_id=current_user.id,
            session_type='analysis',
            input_tokens=len(context.split()) if context else 0,
            output_tokens=0,
            cost_usd=0.0,
            status='in_progress'
        )
        
        db.session.add(session)
        db.session.commit()
        
        # Get AI analysis
        if analysis_type == 'patterns':
            result = AIService.analyze_patterns_with_openai(current_user.id)
        elif analysis_type == 'nutrition':
            result = AIService.analyze_nutrition_patterns(current_user.id, context)
        elif analysis_type == 'mood':
            result = AIService.analyze_mood_patterns(current_user.id, context)
        else:
            result = AIService.get_general_wellness_analysis(current_user.id, context)
        
        if result['success']:
            # Update session with actual usage
            session.output_tokens = result.get('output_tokens', 0)
            session.cost_usd = result.get('cost_usd', 0.0)
            session.status = 'completed'
            session.completed_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'analysis': result.get('analysis', {}),
                'recommendations': result.get('recommendations', []),
                'tokens_used': session.input_tokens + session.output_tokens,
                'cost_usd': session.cost_usd
            })
        else:
            # Update session as failed
            session.status = 'failed'
            session.error_message = result.get('error', 'Unknown error')
            session.completed_at = datetime.utcnow()
            
            db.session.commit()
            
            return jsonify({'success': False, 'error': result.get('error', 'Failed to get AI analysis')}), 500
        
    except Exception as e:
        print(f"❌ Error in AI analysis: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500


@ai_bp.route('/ai/usage', methods=['GET'])
@login_required
def get_ai_usage():
    """Get user's AI usage statistics"""
    try:
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get usage for current month
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        sessions = AIUsageSession.query.filter(
            AIUsageSession.user_id == current_user.id,
            AIUsageSession.created_at >= current_month,
            AIUsageSession.status == 'completed'
        ).all()
        
        total_tokens = sum(session.input_tokens + session.output_tokens for session in sessions)
        total_cost = sum(session.cost_usd for session in sessions)
        total_sessions = len(sessions)
        
        # Get usage by type
        chat_sessions = [s for s in sessions if s.session_type == 'chat']
        analysis_sessions = [s for s in sessions if s.session_type == 'analysis']
        
        usage_stats = {
            'total_tokens': total_tokens,
            'total_cost_usd': total_cost,
            'total_sessions': total_sessions,
            'chat_sessions': len(chat_sessions),
            'analysis_sessions': len(analysis_sessions),
            'chat_tokens': sum(s.input_tokens + s.output_tokens for s in chat_sessions),
            'analysis_tokens': sum(s.input_tokens + s.output_tokens for s in analysis_sessions),
            'chat_cost': sum(s.cost_usd for s in chat_sessions),
            'analysis_cost': sum(s.cost_usd for s in analysis_sessions)
        }
        
        return jsonify({
            'success': True,
            'usage': usage_stats
        })
        
    except Exception as e:
        print(f"❌ Error getting AI usage: {e}")
        return jsonify({'success': False, 'error': 'Failed to get usage statistics'}), 500


@ai_bp.route('/ai/sessions', methods=['GET'])
@login_required
def get_ai_sessions():
    """Get user's AI session history"""
    try:
        current_user = UserService.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get recent sessions
        sessions = AIUsageSession.query.filter_by(
            user_id=current_user.id
        ).order_by(AIUsageSession.created_at.desc()).limit(50).all()
        
        results = []
        for session in sessions:
            results.append({
                'id': session.id,
                'session_type': session.session_type,
                'status': session.status,
                'input_tokens': session.input_tokens,
                'output_tokens': session.output_tokens,
                'total_tokens': session.input_tokens + session.output_tokens,
                'cost_usd': session.cost_usd,
                'created_at': session.created_at.isoformat(),
                'completed_at': session.completed_at.isoformat() if session.completed_at else None,
                'error_message': session.error_message
            })
        
        return jsonify({
            'success': True,
            'sessions': results
        })
        
    except Exception as e:
        print(f"❌ Error getting AI sessions: {e}")
        return jsonify({'success': False, 'error': 'Failed to get session history'}), 500
