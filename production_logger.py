"""Production-ready logging system"""
import logging
import logging.handlers
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from config import config

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        if hasattr(record, 'query'):
            log_entry['query'] = record.query
        if hasattr(record, 'file_name'):
            log_entry['file_name'] = record.file_name
        if hasattr(record, 'processing_time'):
            log_entry['processing_time'] = record.processing_time
        
        return json.dumps(log_entry)

class ProductionLogger:
    """Production-ready logging manager"""
    
    def __init__(self):
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Ensure logs directory exists
        config.ensure_directories()
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        if config.LOG_FORMAT == 'json':
            console_handler.setFormatter(JSONFormatter())
        else:
            console_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
        
        root_logger.addHandler(console_handler)
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            config.LOGS_DIR / 'application.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
        
        if config.LOG_FORMAT == 'json':
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
        
        root_logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.handlers.RotatingFileHandler(
            config.LOGS_DIR / 'errors.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter() if config.LOG_FORMAT == 'json' else
                                   logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        
        root_logger.addHandler(error_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger instance"""
        if name not in self.loggers:
            logger = logging.getLogger(name)
            self.loggers[name] = logger
        return self.loggers[name]
    
    def log_interaction(self, query: str, response: str, 
                       session_id: Optional[str] = None,
                       processing_time: Optional[float] = None,
                       user_id: Optional[str] = None):
        """Log user interaction with structured data"""
        logger = self.get_logger('interactions')
        
        extra = {
            'query': query[:500],  # Truncate long queries
            'response_length': len(response),
            'session_id': session_id,
            'user_id': user_id,
            'processing_time': processing_time
        }
        
        logger.info("User interaction", extra=extra)
    
    def log_file_upload(self, filename: str, file_size: int, 
                       session_id: Optional[str] = None,
                       processing_time: Optional[float] = None):
        """Log file upload event"""
        logger = self.get_logger('file_operations')
        
        extra = {
            'file_name': filename,
            'file_size': file_size,
            'session_id': session_id,
            'processing_time': processing_time
        }
        
        logger.info("File uploaded", extra=extra)
    
    def log_search_query(self, query: str, results_count: int,
                        search_time: float, session_id: Optional[str] = None):
        """Log search query performance"""
        logger = self.get_logger('search')
        
        extra = {
            'query': query[:200],
            'results_count': results_count,
            'search_time': search_time,
            'session_id': session_id
        }
        
        logger.info("Search query executed", extra=extra)
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None):
        """Log errors with context"""
        logger = self.get_logger('errors')
        
        extra = context or {}
        extra['error_type'] = type(error).__name__
        extra['error_message'] = str(error)
        
        logger.error(f"Application error: {error}", extra=extra, exc_info=True)
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related events"""
        logger = self.get_logger('security')
        
        extra = details.copy()
        extra['event_type'] = event_type
        
        logger.warning(f"Security event: {event_type}", extra=extra)

# Global logger instance
prod_logger = ProductionLogger()

# Convenience functions
def get_logger(name: str) -> logging.Logger:
    return prod_logger.get_logger(name)

def log_interaction(query: str, response: str, **kwargs):
    return prod_logger.log_interaction(query, response, **kwargs)

def log_file_upload(filename: str, file_size: int, **kwargs):
    return prod_logger.log_file_upload(filename, file_size, **kwargs)

def log_search_query(query: str, results_count: int, search_time: float, **kwargs):
    return prod_logger.log_search_query(query, results_count, search_time, **kwargs)

def log_error(error: Exception, context: Dict[str, Any] = None):
    return prod_logger.log_error(error, context)

def log_security_event(event_type: str, details: Dict[str, Any]):
    return prod_logger.log_security_event(event_type, details)