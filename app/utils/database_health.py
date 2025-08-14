"""
Ki Wellness - Database Health Monitoring
========================================

This module provides database health checks and monitoring utilities
to help detect and diagnose database connection issues in production.

Author: Ki Wellness Team
Version: 1.0
"""

import logging
from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DisconnectionError
from typing import Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseHealthMonitor:
    """Database health monitoring and diagnostics"""
    
    def __init__(self, db):
        self.db = db
        self.last_check = None
        self.check_interval = timedelta(minutes=5)  # Check every 5 minutes
        self.health_status = {
            'last_check': None,
            'status': 'unknown',
            'response_time_ms': None,
            'error_count': 0,
            'last_error': None,
            'connection_string': None
        }
    
    def check_database_health(self, force_check: bool = False) -> Dict[str, Any]:
        """
        Perform a comprehensive database health check
        
        Args:
            force_check: Force check even if within interval
            
        Returns:
            Dict containing health status
        """
        now = datetime.utcnow()
        
        # Skip if within check interval (unless forced)
        if (not force_check and 
            self.last_check and 
            now - self.last_check < self.check_interval):
            return self.health_status
        
        start_time = datetime.utcnow()
        
        try:
            # Check if we're in an application context
            try:
                # Get database connection info
                db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', 'unknown')
                self.health_status['connection_string'] = self._mask_password(db_uri)
            except RuntimeError:
                # Not in application context
                self.health_status.update({
                    'last_check': now.isoformat(),
                    'status': 'no_app_context',
                    'response_time_ms': None,
                    'error_count': self.health_status.get('error_count', 0) + 1,
                    'last_error': 'No Flask application context available'
                })
                logger.warning("⚠️  Database health check called outside application context")
                self.last_check = now
                return self.health_status
            
            # Test basic connectivity
            with self.db.engine.connect() as connection:
                # Simple query test
                result = connection.execute(text('SELECT 1 as test'))
                result.fetchone()
                
                # Test database version
                if 'postgresql' in db_uri.lower():
                    version_result = connection.execute(text('SELECT version()'))
                    version = version_result.fetchone()[0]
                    self.health_status['database_version'] = version
                elif 'sqlite' in db_uri.lower():
                    version_result = connection.execute(text('SELECT sqlite_version()'))
                    version = version_result.fetchone()[0]
                    self.health_status['database_version'] = f"SQLite {version}"
            
            # Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Update health status
            self.health_status.update({
                'last_check': now.isoformat(),
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'error_count': 0,
                'last_error': None
            })
            
            logger.info(f"✅ Database health check passed - Response time: {response_time:.2f}ms")
            
        except (SQLAlchemyError, OperationalError, DisconnectionError) as e:
            # Database error occurred
            self.health_status.update({
                'last_check': now.isoformat(),
                'status': 'unhealthy',
                'response_time_ms': None,
                'error_count': self.health_status.get('error_count', 0) + 1,
                'last_error': str(e)
            })
            
            logger.error(f"❌ Database health check failed: {e}")
            
        except Exception as e:
            # Unexpected error
            self.health_status.update({
                'last_check': now.isoformat(),
                'status': 'error',
                'response_time_ms': None,
                'error_count': self.health_status.get('error_count', 0) + 1,
                'last_error': str(e)
            })
            
            logger.error(f"❌ Unexpected error during database health check: {e}")
        
        self.last_check = now
        return self.health_status
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status (cached if recent)"""
        return self.check_database_health(force_check=False)
    
    def force_health_check(self) -> Dict[str, Any]:
        """Force a fresh health check"""
        return self.check_database_health(force_check=True)
    
    def is_healthy(self) -> bool:
        """Check if database is currently healthy"""
        status = self.get_health_status()
        return status.get('status') == 'healthy'
    
    def log_health_status(self):
        """Log current health status"""
        status = self.get_health_status()
        
        if status['status'] == 'healthy':
            logger.info(f"🗄️  Database Status: {status['status'].upper()} | "
                       f"Response: {status['response_time_ms']}ms | "
                       f"Last Check: {status['last_check']}")
        else:
            logger.error(f"🗄️  Database Status: {status['status'].upper()} | "
                        f"Error: {status['last_error']} | "
                        f"Error Count: {status['error_count']}")
    
    def _mask_password(self, connection_string: str) -> str:
        """Mask password in connection string for logging"""
        if not connection_string:
            return 'unknown'
        
        # Simple password masking for common formats
        if '://' in connection_string:
            parts = connection_string.split('://')
            if len(parts) == 2:
                protocol = parts[0]
                rest = parts[1]
                
                # Mask password in PostgreSQL/SQLite URLs
                if '@' in rest:
                    user_pass, host_part = rest.split('@', 1)
                    if ':' in user_pass:
                        user, _ = user_pass.split(':', 1)
                        return f"{protocol}://{user}:***@{host_part}"
                
                return f"{protocol}://***"
        
        return '***'
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Get comprehensive database diagnostics"""
        health = self.get_health_status()
        
        diagnostics = {
            'timestamp': datetime.utcnow().isoformat(),
            'health_status': health,
            'environment': {
                'flask_env': current_app.config.get('FLASK_ENV', 'unknown'),
                'debug_mode': current_app.config.get('DEBUG', False),
                'database_type': self._get_database_type(),
            },
            'connection_info': {
                'pool_size': getattr(self.db.engine, 'pool_size', 'unknown'),
                'max_overflow': getattr(self.db.engine, 'max_overflow', 'unknown'),
                'pool_timeout': getattr(self.db.engine, 'pool_timeout', 'unknown'),
            }
        }
        
        return diagnostics
    
    def _get_database_type(self) -> str:
        """Get database type from connection string"""
        db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
        
        if 'postgresql' in db_uri.lower():
            return 'PostgreSQL'
        elif 'sqlite' in db_uri.lower():
            return 'SQLite'
        elif 'mysql' in db_uri.lower():
            return 'MySQL'
        else:
            return 'Unknown'

# Global health monitor instance
health_monitor: Optional[DatabaseHealthMonitor] = None

def init_health_monitor(db):
    """Initialize the global health monitor"""
    global health_monitor
    health_monitor = DatabaseHealthMonitor(db)
    logger.info("🔧 Database health monitor initialized")
    return health_monitor

def get_health_monitor() -> Optional[DatabaseHealthMonitor]:
    """Get the global health monitor instance"""
    return health_monitor

def log_database_health():
    """Log current database health status"""
    if health_monitor:
        health_monitor.log_health_status()

def check_database_health() -> Dict[str, Any]:
    """Check database health and return status"""
    if health_monitor:
        return health_monitor.get_health_status()
    return {'status': 'monitor_not_initialized'}

def is_database_healthy() -> bool:
    """Check if database is healthy"""
    if health_monitor:
        return health_monitor.is_healthy()
    return False

def safe_check_database_health() -> Dict[str, Any]:
    """Safely check database health with proper error handling"""
    try:
        return check_database_health()
    except Exception as e:
        logger.error(f"❌ Error during safe database health check: {e}")
        return {
            'status': 'error',
            'last_error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
