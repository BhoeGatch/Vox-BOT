"""Production-ready exception handling utilities"""
import functools
import traceback
import time
from typing import Callable, Any, Optional, Dict
from production_logger import log_error, get_logger

logger = get_logger('exception_handler')

class AppError(Exception):
    """Base application error"""
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        super().__init__(message)
        self.error_code = error_code or 'APP_ERROR'
        self.details = details or {}

class FileProcessingError(AppError):
    """File processing related errors"""
    def __init__(self, message: str, filename: str = None, **kwargs):
        super().__init__(message, 'FILE_ERROR', kwargs)
        self.filename = filename

class SearchError(AppError):
    """Search engine related errors"""
    def __init__(self, message: str, query: str = None, **kwargs):
        super().__init__(message, 'SEARCH_ERROR', kwargs)
        self.query = query

class ValidationError(AppError):
    """Validation related errors"""
    def __init__(self, message: str, field: str = None, **kwargs):
        super().__init__(message, 'VALIDATION_ERROR', kwargs)
        self.field = field

def handle_exceptions(operation_name: str = None, 
                     default_return=None,
                     log_errors: bool = True,
                     reraise: bool = False):
    """Decorator for comprehensive exception handling"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                
                # Log successful operations
                execution_time = time.time() - start_time
                logger.info(f"Operation completed: {op_name}", extra={
                    'operation': op_name,
                    'execution_time': execution_time,
                    'success': True
                })
                
                return result
                
            except (ValidationError, FileProcessingError, SearchError) as e:
                # Handle known application errors
                execution_time = time.time() - start_time
                
                if log_errors:
                    logger.warning(f"Application error in {op_name}: {e}", extra={
                        'operation': op_name,
                        'execution_time': execution_time,
                        'error_code': e.error_code,
                        'error_details': e.details
                    })
                
                if reraise:
                    raise
                return default_return
                
            except Exception as e:
                # Handle unexpected errors
                execution_time = time.time() - start_time
                
                if log_errors:
                    log_error(e, {
                        'operation': op_name,
                        'execution_time': execution_time,
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys())
                    })
                
                logger.error(f"Unexpected error in {op_name}: {e}", extra={
                    'operation': op_name,
                    'execution_time': execution_time,
                    'error_type': type(e).__name__
                })
                
                if reraise:
                    raise
                return default_return
        
        return wrapper
    return decorator

def safe_execute(func: Callable, *args, default_return=None, 
                operation_name: str = None, **kwargs) -> tuple[Any, Optional[Exception]]:
    """Safely execute a function and return result and any exception"""
    try:
        result = func(*args, **kwargs)
        return result, None
    except Exception as e:
        op_name = operation_name or f"{func.__name__}"
        log_error(e, {
            'operation': op_name,
            'function': func.__name__
        })
        return default_return, e

class CircuitBreaker:
    """Circuit breaker pattern for handling repeated failures"""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time < self.timeout:
                raise AppError("Circuit breaker is OPEN", "CIRCUIT_BREAKER_OPEN")
            else:
                self.state = 'HALF_OPEN'
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, 
                    backoff_factor: float = 2.0,
                    exceptions: tuple = (Exception,)):
    """Decorator to retry function on failure"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"Function {func.__name__} failed after {max_retries + 1} attempts")
                        break
                    
                    wait_time = delay * (backoff_factor ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}, retrying in {wait_time}s")
                    time.sleep(wait_time)
            
            raise last_exception
        
        return wrapper
    return decorator

# Global circuit breaker instances for different operations
file_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30)
search_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)