"""
Ki Wellness - Admin Routes
==========================

This module contains admin panel routes for system management,
user administration, and system monitoring.

Author: Ki Wellness Team
Version: 2.0
"""

from flask import Blueprint, render_template, request, jsonify
from datetime import datetime, timedelta
from ..models import db, User, UserProfile, Review, SystemSettings, TokenUsage, APICosts
from ..services import UserService, SystemService
from ..decorators import admin_required
from ..config import get_stripe_config, STRIPE_AVAILABLE

# Create blueprint
admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard page"""
    return render_template('admin_dashboard.html')


@admin_bp.route('/admin/reviews/<int:review_id>/approve', methods=['POST'])
@admin_required
def approve_review(review_id):
    """Approve a review"""
    try:
        review = Review.query.get(review_id)
        if not review:
            return jsonify({'success': False, 'error': 'Review not found'}), 404
        
        review.is_approved = True
        review.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Review approved successfully!'
        })
        
    except Exception as e:
        print(f"❌ Error approving review: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to approve review'}), 500


@admin_bp.route('/admin/reviews/<int:review_id>/reject', methods=['POST'])
@admin_required
def reject_review(review_id):
    """Reject a review"""
    try:
        review = Review.query.get(review_id)
        if not review:
            return jsonify({'success': False, 'error': 'Review not found'}), 404
        
        review.is_approved = False
        review.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Review rejected successfully!'
        })
        
    except Exception as e:
        print(f"❌ Error rejecting review: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to reject review'}), 500


@admin_bp.route('/admin/users/<int:user_id>/suspend', methods=['POST'])
@admin_required
def suspend_user(user_id):
    """Suspend a user account"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        if user.is_admin:
            return jsonify({'success': False, 'error': 'Cannot suspend admin accounts'}), 403
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User {user.username} suspended successfully!'
        })
        
    except Exception as e:
        print(f"❌ Error suspending user: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to suspend user'}), 500


@admin_bp.route('/admin/users/<int:user_id>/activate', methods=['POST'])
@admin_required
def activate_user(user_id):
    """Activate a suspended user account"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user.is_active = True
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User {user.username} activated successfully!'
        })
        
    except Exception as e:
        print(f"❌ Error activating user: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to activate user'}), 500


@admin_bp.route('/admin/users/<int:user_id>/promote', methods=['POST'])
@admin_required
def promote_user(user_id):
    """Promote a user to admin"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user.is_admin = True
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User {user.username} promoted to admin successfully!'
        })
        
    except Exception as e:
        print(f"❌ Error promoting user: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to promote user'}), 500


@admin_bp.route('/admin/users/<int:user_id>/demote', methods=['POST'])
@admin_required
def demote_user(user_id):
    """Demote an admin to regular user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Prevent demoting the main admin account
        if user.username == 'ki.wellness':
            return jsonify({'success': False, 'error': 'Cannot demote main admin account'}), 403
        
        user.is_admin = False
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User {user.username} demoted successfully!'
        })
        
    except Exception as e:
        print(f"❌ Error demoting user: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to demote user'}), 500


@admin_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete a user account"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Prevent deleting the main admin account
        if user.username == 'ki.wellness':
            return jsonify({'success': False, 'error': 'Cannot delete main admin account'}), 403
        
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'User {username} deleted successfully!'
        })
        
    except Exception as e:
        print(f"❌ Error deleting user: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to delete user'}), 500


@admin_bp.route('/admin/system/health')
@admin_required
def system_health():
    """Get system health information"""
    try:
        # Get basic system stats
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        total_reviews = Review.query.count()
        pending_reviews = Review.query.filter_by(is_approved=None).count()
        
        # Get recent activity
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        recent_reviews = Review.query.order_by(Review.created_at.desc()).limit(5).all()
        
        health_data = {
            'total_users': total_users,
            'active_users': active_users,
            'total_reviews': total_reviews,
            'pending_reviews': pending_reviews,
            'recent_users': [
                {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'created_at': user.created_at.isoformat(),
                    'is_active': user.is_active
                } for user in recent_users
            ],
            'recent_reviews': [
                {
                    'id': review.id,
                    'name': review.name,
                    'rating': review.rating,
                    'content': review.content[:100] + '...' if len(review.content) > 100 else review.content,
                    'created_at': review.created_at.isoformat(),
                    'is_approved': review.is_approved
                } for review in recent_reviews
            ]
        }
        
        return jsonify({
            'success': True,
            'health': health_data
        })
        
    except Exception as e:
        print(f"❌ Error getting system health: {e}")
        return jsonify({'success': False, 'error': 'Failed to get system health'}), 500


@admin_bp.route('/admin/system/settings', methods=['GET', 'POST'])
@admin_required
def system_settings():
    """Get or update system settings"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            current_admin = UserService.get_current_user()
            
            # Update settings
            for key, value in data.items():
                SystemService.set_system_setting(key, str(value), updated_by=current_admin.id)
            
            return jsonify({
                'success': True,
                'message': 'System settings updated successfully!'
            })
        else:
            # Get all settings
            settings = SystemSettings.query.all()
            settings_dict = {setting.key: setting.value for setting in settings}
            
            return jsonify({
                'success': True,
                'settings': settings_dict
            })
        
    except Exception as e:
        print(f"❌ Error with system settings: {e}")
        return jsonify({'success': False, 'error': 'Failed to manage system settings'}), 500


@admin_bp.route('/admin/system/emergency-stop', methods=['POST'])
@admin_required
def emergency_stop():
    """Emergency stop for OpenAI API"""
    try:
        current_admin = UserService.get_current_user()
        SystemService.set_system_setting('emergency_stop_active', 'true', updated_by=current_admin.id)
        
        return jsonify({
            'success': True,
            'message': 'Emergency stop activated! OpenAI API calls are now disabled.'
        })
        
    except Exception as e:
        print(f"❌ Error activating emergency stop: {e}")
        return jsonify({'success': False, 'error': 'Failed to activate emergency stop'}), 500


@admin_bp.route('/admin/system/update-gpt-model', methods=['POST'])
@admin_required
def update_gpt_model():
    """Update the GPT model being used"""
    try:
        data = request.get_json()
        model = data.get('model')
        
        if not model:
            return jsonify({'success': False, 'error': 'Model is required'}), 400
        
        current_admin = UserService.get_current_user()
        SystemService.set_system_setting('current_gpt_model', model, updated_by=current_admin.id)
        
        return jsonify({
            'success': True,
            'message': f'GPT model updated to {model}'
        })
        
    except Exception as e:
        print(f"❌ Error updating GPT model: {e}")
        return jsonify({'success': False, 'error': 'Failed to update GPT model'}), 500


@admin_bp.route('/admin/system/update-token-limit', methods=['POST'])
@admin_required
def update_token_limit():
    """Update monthly token limit"""
    try:
        data = request.get_json()
        limit = data.get('limit')
        
        if not limit or not str(limit).isdigit():
            return jsonify({'success': False, 'error': 'Valid limit is required'}), 400
        
        current_admin = UserService.get_current_user()
        SystemService.set_system_setting('monthly_token_limit', str(limit), updated_by=current_admin.id)
        
        return jsonify({
            'success': True,
            'message': f'Monthly token limit updated to {limit}'
        })
        
    except Exception as e:
        print(f"❌ Error updating token limit: {e}")
        return jsonify({'success': False, 'error': 'Failed to update token limit'}), 500


@admin_bp.route('/admin/system/toggle-account-creation', methods=['POST'])
@admin_required
def toggle_account_creation():
    """Toggle new account creation"""
    try:
        current_setting = SystemService.get_system_setting('new_accounts_enabled', 'true')
        new_value = 'false' if current_setting == 'true' else 'true'
        
        current_admin = UserService.get_current_user()
        SystemService.set_system_setting('new_accounts_enabled', new_value, updated_by=current_admin.id)
        
        status = 'enabled' if new_value == 'true' else 'disabled'
        return jsonify({
            'success': True,
            'message': f'New account creation {status}'
        })
        
    except Exception as e:
        print(f"❌ Error toggling account creation: {e}")
        return jsonify({'success': False, 'error': 'Failed to toggle account creation'}), 500


@admin_bp.route('/admin/system/update-flexible-tier', methods=['POST'])
@admin_required
def update_flexible_tier():
    """Update flexible service tier setting"""
    try:
        data = request.get_json()
        enabled = data.get('enabled')
        
        if enabled is None:
            return jsonify({'success': False, 'error': 'Enabled status is required'}), 400
        
        current_admin = UserService.get_current_user()
        SystemService.set_system_setting('flexible_service_tier', str(enabled).lower(), updated_by=current_admin.id)
        
        status = 'enabled' if enabled else 'disabled'
        return jsonify({
            'success': True,
            'message': f'Flexible service tier {status}'
        })
        
    except Exception as e:
        print(f"❌ Error updating flexible tier: {e}")
        return jsonify({'success': False, 'error': 'Failed to update flexible tier'}), 500


@admin_bp.route('/admin/system/toggle-payment-testing', methods=['POST'])
@admin_required
def toggle_payment_testing():
    """Toggle payment testing mode"""
    try:
        current_setting = SystemService.get_system_setting('payment_testing_mode', 'false')
        new_value = 'true' if current_setting == 'false' else 'false'
        
        current_admin = UserService.get_current_user()
        SystemService.set_system_setting('payment_testing_mode', new_value, updated_by=current_admin.id)
        
        mode = 'sandbox' if new_value == 'true' else 'live'
        return jsonify({
            'success': True,
            'message': f'Payment mode switched to {mode}'
        })
        
    except Exception as e:
        print(f"❌ Error toggling payment testing: {e}")
        return jsonify({'success': False, 'error': 'Failed to toggle payment testing'}), 500


@admin_bp.route('/admin/users/search')
@admin_required
def search_users():
    """Search users"""
    try:
        query = request.args.get('q', '').strip()
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query is required'}), 400
        
        # Search users
        users = User.query.filter(
            (User.username.ilike(f'%{query}%')) |
            (User.email.ilike(f'%{query}%'))
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        results = []
        for user in users.items:
            profile = UserProfile.query.filter_by(user_id=user.id).first()
            results.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'name': profile.name if profile else None,
                'is_active': user.is_active,
                'is_admin': user.is_admin,
                'created_at': user.created_at.isoformat(),
                'last_login': user.updated_at.isoformat() if user.updated_at else None
            })
        
        return jsonify({
            'success': True,
            'users': results,
            'total': users.total,
            'pages': users.pages,
            'current_page': page
        })
        
    except Exception as e:
        print(f"❌ Error searching users: {e}")
        return jsonify({'success': False, 'error': 'Failed to search users'}), 500


@admin_bp.route('/admin/accounting/token-usage')
@admin_required
def token_usage_report():
    """Get token usage report"""
    try:
        # Get date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = TokenUsage.query
        
        if start_date:
            query = query.filter(TokenUsage.created_at >= start_date)
        if end_date:
            query = query.filter(TokenUsage.created_at <= end_date)
        
        usage_data = query.all()
        
        total_tokens = sum(entry.tokens_used for entry in usage_data)
        total_cost = sum(entry.cost_usd for entry in usage_data)
        
        # Group by user
        user_usage = {}
        for entry in usage_data:
            if entry.user_id not in user_usage:
                user_usage[entry.user_id] = {
                    'tokens_used': 0,
                    'cost_usd': 0.0,
                    'sessions': 0
                }
            user_usage[entry.user_id]['tokens_used'] += entry.tokens_used
            user_usage[entry.user_id]['cost_usd'] += entry.cost_usd
            user_usage[entry.user_id]['sessions'] += 1
        
        return jsonify({
            'success': True,
            'report': {
                'total_tokens': total_tokens,
                'total_cost_usd': total_cost,
                'total_sessions': len(usage_data),
                'user_usage': user_usage
            }
        })
        
    except Exception as e:
        print(f"❌ Error getting token usage report: {e}")
        return jsonify({'success': False, 'error': 'Failed to get token usage report'}), 500


@admin_bp.route('/admin/accounting/profit-loss')
@admin_required
def profit_loss_report():
    """Get profit/loss report"""
    try:
        # This would integrate with Stripe to get actual revenue data
        # For now, return a placeholder structure
        
        return jsonify({
            'success': True,
            'report': {
                'total_revenue': 0.0,
                'total_costs': 0.0,
                'net_profit': 0.0,
                'period': 'current_month'
            }
        })
        
    except Exception as e:
        print(f"❌ Error getting profit/loss report: {e}")
        return jsonify({'success': False, 'error': 'Failed to get profit/loss report'}), 500


@admin_bp.route('/admin/accounting/api-costs', methods=['GET', 'POST'])
@admin_required
def api_costs():
    """Get or update API costs"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            current_admin = UserService.get_current_user()
            
            # Update API costs
            for cost_data in data:
                api_cost = APICosts.query.filter_by(model_name=cost_data['model_name']).first()
                if api_cost:
                    api_cost.input_cost_per_1k = cost_data['input_cost_per_1k']
                    api_cost.output_cost_per_1k = cost_data['output_cost_per_1k']
                    api_cost.updated_by = current_admin.id
                    api_cost.updated_at = datetime.utcnow()
                else:
                    api_cost = APICosts(
                        model_name=cost_data['model_name'],
                        input_cost_per_1k=cost_data['input_cost_per_1k'],
                        output_cost_per_1k=cost_data['output_cost_per_1k'],
                        updated_by=current_admin.id
                    )
                    db.session.add(api_cost)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'API costs updated successfully!'
            })
        else:
            # Get all API costs
            costs = APICosts.query.all()
            costs_data = [
                {
                    'id': cost.id,
                    'model_name': cost.model_name,
                    'input_cost_per_1k': cost.input_cost_per_1k,
                    'output_cost_per_1k': cost.output_cost_per_1k,
                    'updated_at': cost.updated_at.isoformat() if cost.updated_at else None
                } for cost in costs
            ]
            
            return jsonify({
                'success': True,
                'costs': costs_data
            })
        
    except Exception as e:
        print(f"❌ Error with API costs: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to manage API costs'}), 500
