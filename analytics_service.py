#!/usr/bin/env python3
"""
Analytics Service for Ki Wellness
Handles AI usage tracking, cost analysis, and revenue analytics
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal
from database import db, AIUsageLog, RevenueLog, User, Subscription
from sqlalchemy import func, and_

class AnalyticsService:
    """Service for handling analytics and cost tracking"""
    
    @staticmethod
    def log_ai_usage(
        user_id: int,
        model_used: str,
        input_tokens: int,
        output_tokens: int,
        input_cost: float,
        output_cost: float,
        endpoint: str,
        response_time_ms: int,
        success: bool = True,
        error_message: str = None
    ) -> AIUsageLog:
        """Log AI usage for cost tracking and analytics"""
        try:
            # Calculate total cost
            total_cost = input_cost + output_cost
            
            # Create unique session ID
            session_id = str(uuid.uuid4())
            
            # Create usage log entry
            usage_log = AIUsageLog(
                user_id=user_id,
                session_id=session_id,
                model_used=model_used,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                input_cost=Decimal(str(input_cost)),
                output_cost=Decimal(str(output_cost)),
                total_cost=Decimal(str(total_cost)),
                endpoint=endpoint,
                response_time_ms=response_time_ms,
                success=success,
                error_message=error_message
            )
            
            db.session.add(usage_log)
            db.session.commit()
            
            print(f"📊 AI Usage logged: {model_used} - Input: {input_tokens}, Output: {output_tokens}, Cost: ${total_cost:.6f}")
            return usage_log
            
        except Exception as e:
            print(f"❌ Error logging AI usage: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def log_revenue(
        user_id: Optional[int],
        revenue_type: str,
        amount: float,
        currency: str = 'USD',
        stripe_payment_intent_id: str = None,
        stripe_subscription_id: str = None,
        description: str = None,
        status: str = 'completed'
    ) -> RevenueLog:
        """Log revenue for analytics"""
        try:
            revenue_log = RevenueLog(
                user_id=user_id,
                revenue_type=revenue_type,
                amount=Decimal(str(amount)),
                currency=currency,
                stripe_payment_intent_id=stripe_payment_intent_id,
                stripe_subscription_id=stripe_subscription_id,
                description=description,
                status=status
            )
            
            db.session.add(revenue_log)
            db.session.commit()
            
            print(f"💰 Revenue logged: {revenue_type} - ${amount} {currency}")
            return revenue_log
            
        except Exception as e:
            print(f"❌ Error logging revenue: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_ai_usage_summary(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get AI usage summary for analytics"""
        try:
            query = db.session.query(AIUsageLog)
            
            # Apply filters
            if start_date:
                query = query.filter(AIUsageLog.created_at >= start_date)
            if end_date:
                query = query.filter(AIUsageLog.created_at <= end_date)
            if user_id:
                query = query.filter(AIUsageLog.user_id == user_id)
            
            # Get summary statistics
            total_requests = query.count()
            successful_requests = query.filter(AIUsageLog.success == True).count()
            failed_requests = total_requests - successful_requests
            
            # Get cost totals
            cost_summary = query.with_entities(
                func.sum(AIUsageLog.input_cost).label('total_input_cost'),
                func.sum(AIUsageLog.output_cost).label('total_output_cost'),
                func.sum(AIUsageLog.total_cost).label('total_cost'),
                func.sum(AIUsageLog.input_tokens).label('total_input_tokens'),
                func.sum(AIUsageLog.output_tokens).label('total_output_tokens')
            ).first()
            
            # Get model breakdown
            model_breakdown = query.with_entities(
                AIUsageLog.model_used,
                func.count(AIUsageLog.id).label('request_count'),
                func.sum(AIUsageLog.total_cost).label('total_cost'),
                func.avg(AIUsageLog.response_time_ms).label('avg_response_time')
            ).group_by(AIUsageLog.model_used).all()
            
            # Get daily breakdown
            daily_breakdown = query.with_entities(
                func.date(AIUsageLog.created_at).label('date'),
                func.count(AIUsageLog.id).label('request_count'),
                func.sum(AIUsageLog.total_cost).label('total_cost')
            ).group_by(func.date(AIUsageLog.created_at)).order_by(func.date(AIUsageLog.created_at)).all()
            
            return {
                'summary': {
                    'total_requests': total_requests,
                    'successful_requests': successful_requests,
                    'failed_requests': failed_requests,
                    'success_rate': (successful_requests / total_requests * 100) if total_requests > 0 else 0
                },
                'costs': {
                    'total_input_cost': float(cost_summary.total_input_cost or 0),
                    'total_output_cost': float(cost_summary.total_output_cost or 0),
                    'total_cost': float(cost_summary.total_cost or 0),
                    'total_input_tokens': int(cost_summary.total_input_tokens or 0),
                    'total_output_tokens': int(cost_summary.total_output_tokens or 0)
                },
                'model_breakdown': [
                    {
                        'model': item.model_used,
                        'request_count': item.request_count,
                        'total_cost': float(item.total_cost or 0),
                        'avg_response_time': float(item.avg_response_time or 0)
                    }
                    for item in model_breakdown
                ],
                'daily_breakdown': [
                    {
                        'date': item.date.isoformat() if item.date else None,
                        'request_count': item.request_count,
                        'total_cost': float(item.total_cost or 0)
                    }
                    for item in daily_breakdown
                ]
            }
            
        except Exception as e:
            print(f"❌ Error getting AI usage summary: {e}")
            return {}
    
    @staticmethod
    def get_revenue_summary(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get revenue summary for analytics"""
        try:
            query = db.session.query(RevenueLog)
            
            # Apply filters
            if start_date:
                query = query.filter(RevenueLog.created_at >= start_date)
            if end_date:
                query = query.filter(RevenueLog.created_at <= end_date)
            if user_id:
                query = query.filter(RevenueLog.user_id == user_id)
            
            # Get summary statistics
            total_revenue = query.filter(RevenueLog.status == 'completed').with_entities(
                func.sum(RevenueLog.amount)
            ).scalar() or 0
            
            # Get revenue by type
            revenue_by_type = query.filter(RevenueLog.status == 'completed').with_entities(
                RevenueLog.revenue_type,
                func.sum(RevenueLog.amount).label('total_amount'),
                func.count(RevenueLog.id).label('transaction_count')
            ).group_by(RevenueLog.revenue_type).all()
            
            # Get monthly breakdown
            monthly_breakdown = query.filter(RevenueLog.status == 'completed').with_entities(
                func.date_trunc('month', RevenueLog.created_at).label('month'),
                func.sum(RevenueLog.amount).label('total_amount'),
                func.count(RevenueLog.id).label('transaction_count')
            ).group_by(func.date_trunc('month', RevenueLog.created_at)).order_by(func.date_trunc('month', RevenueLog.created_at)).all()
            
            # Get subscription analytics
            subscription_analytics = query.filter(
                and_(
                    RevenueLog.revenue_type == 'subscription',
                    RevenueLog.status == 'completed'
                )
            ).with_entities(
                func.sum(RevenueLog.amount).label('total_subscription_revenue'),
                func.count(RevenueLog.id).label('subscription_transactions')
            ).first()
            
            # Get health coaching analytics
            coaching_analytics = query.filter(
                and_(
                    RevenueLog.revenue_type == 'health_coaching',
                    RevenueLog.status == 'completed'
                )
            ).with_entities(
                func.sum(RevenueLog.amount).label('total_coaching_revenue'),
                func.count(RevenueLog.id).label('coaching_transactions')
            ).first()
            
            return {
                'summary': {
                    'total_revenue': float(total_revenue),
                    'total_transactions': query.count()
                },
                'revenue_by_type': [
                    {
                        'type': item.revenue_type,
                        'total_amount': float(item.total_amount or 0),
                        'transaction_count': item.transaction_count
                    }
                    for item in revenue_by_type
                ],
                'monthly_breakdown': [
                    {
                        'month': item.month.isoformat() if item.month else None,
                        'total_amount': float(item.total_amount or 0),
                        'transaction_count': item.transaction_count
                    }
                    for item in monthly_breakdown
                ],
                'subscription_analytics': {
                    'total_revenue': float(subscription_analytics.total_subscription_revenue or 0),
                    'transaction_count': subscription_analytics.subscription_transactions or 0
                },
                'coaching_analytics': {
                    'total_revenue': float(coaching_analytics.total_coaching_revenue or 0),
                    'transaction_count': coaching_analytics.coaching_transactions or 0
                }
            }
            
        except Exception as e:
            print(f"❌ Error getting revenue summary: {e}")
            return {}
    
    @staticmethod
    def get_monthly_analytics(months_back: int = 12) -> Dict[str, Any]:
        """Get comprehensive monthly analytics"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30 * months_back)
            
            ai_usage = AnalyticsService.get_ai_usage_summary(start_date, end_date)
            revenue = AnalyticsService.get_revenue_summary(start_date, end_date)
            
            # Calculate monthly averages
            months_count = months_back
            avg_monthly_ai_cost = ai_usage.get('costs', {}).get('total_cost', 0) / months_count if months_count > 0 else 0
            avg_monthly_revenue = revenue.get('summary', {}).get('total_revenue', 0) / months_count if months_count > 0 else 0
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'months': months_count
                },
                'ai_usage': ai_usage,
                'revenue': revenue,
                'averages': {
                    'monthly_ai_cost': avg_monthly_ai_cost,
                    'monthly_revenue': avg_monthly_revenue,
                    'profit_margin': avg_monthly_revenue - avg_monthly_ai_cost
                }
            }
            
        except Exception as e:
            print(f"❌ Error getting monthly analytics: {e}")
            return {}

# Global analytics service instance
analytics_service = AnalyticsService()
