"""Input validation and security utilities"""
import re
import hashlib
import magic
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from config import config
from production_logger import log_security_event, get_logger

logger = get_logger('validation')

class ValidationError(Exception):
    """Custom validation error"""
    pass

class SecurityError(Exception):
    """Custom security error"""
    pass

class InputValidator:
    """Production-ready input validation"""
    
    # Dangerous patterns to detect
    DANGEROUS_PATTERNS = [
        r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',  # Script tags
        r'javascript:',  # JavaScript protocols
        r'vbscript:',    # VBScript protocols
        r'onload\s*=',   # Event handlers
        r'onerror\s*=',
        r'onclick\s*=',
        r'\.\./',        # Directory traversal
        r'\\\.\\\.\\',   # Windows directory traversal
        r'<iframe',      # Iframes
        r'<object',      # Objects
        r'<embed',       # Embeds
    ]
    
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)',
        r'(\b(OR|AND)\s+\d+\s*=\s*\d+)',
        r'[\'";].*(-{2}|\/\*)',
    ]
    
    def __init__(self):
        self.compiled_dangerous_patterns = [re.compile(pattern, re.IGNORECASE) 
                                          for pattern in self.DANGEROUS_PATTERNS]
        self.compiled_sql_patterns = [re.compile(pattern, re.IGNORECASE) 
                                    for pattern in self.SQL_INJECTION_PATTERNS]
    
    def validate_query(self, query: str) -> str:
        """Validate and sanitize user query"""
        if not query or not isinstance(query, str):
            raise ValidationError("Query must be a non-empty string")
        
        # Length validation
        if len(query) < config.MIN_QUERY_LENGTH:
            raise ValidationError(f"Query too short. Minimum length: {config.MIN_QUERY_LENGTH}")
        
        if len(query) > config.MAX_QUERY_LENGTH:
            raise ValidationError(f"Query too long. Maximum length: {config.MAX_QUERY_LENGTH}")
        
        # Security validation
        self._check_dangerous_patterns(query, "query")
        self._check_sql_injection(query)
        
        # Sanitize
        sanitized = self._sanitize_text(query)
        
        logger.info("Query validated successfully", extra={'query_length': len(sanitized)})
        return sanitized
    
    def validate_filename(self, filename: str) -> str:
        """Validate and sanitize filename"""
        if not filename or not isinstance(filename, str):
            raise ValidationError("Filename must be a non-empty string")
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
        if any(char in filename for char in dangerous_chars):
            raise SecurityError(f"Filename contains dangerous characters: {filename}")
        
        # Check for reserved names (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        
        name_without_ext = Path(filename).stem.upper()
        if name_without_ext in reserved_names:
            raise SecurityError(f"Filename uses reserved name: {filename}")
        
        # Check extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in config.ALLOWED_EXTENSIONS:
            raise ValidationError(f"File extension not allowed. Allowed: {config.ALLOWED_EXTENSIONS}")
        
        # Length check
        if len(filename) > 255:
            raise ValidationError("Filename too long")
        
        logger.info("Filename validated successfully", extra={'filename': filename})
        return filename
    
    def validate_file_content(self, file_path: Path, max_size: int = None) -> Dict[str, Any]:
        """Validate file content and properties"""
        if not file_path.exists():
            raise ValidationError("File does not exist")
        
        file_stats = file_path.stat()
        file_size = file_stats.st_size
        max_size = max_size or config.MAX_FILE_SIZE
        
        # Size validation
        if file_size > max_size:
            raise ValidationError(f"File too large. Maximum size: {max_size / (1024*1024):.1f}MB")
        
        if file_size == 0:
            raise ValidationError("File is empty")
        
        # File type validation using python-magic
        try:
            file_type = magic.from_file(str(file_path), mime=True)
            file_signature = magic.from_file(str(file_path))
        except Exception as e:
            logger.warning(f"Could not determine file type for {file_path}: {e}")
            file_type = "unknown"
            file_signature = "unknown"
        
        # Validate MIME type matches extension
        expected_types = {
            '.pdf': ['application/pdf'],
            '.docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            '.txt': ['text/plain', 'text/x-python', 'application/x-empty']
        }
        
        file_ext = file_path.suffix.lower()
        if file_ext in expected_types and file_type not in expected_types[file_ext]:
            log_security_event("file_type_mismatch", {
                'filename': file_path.name,
                'expected_types': expected_types[file_ext],
                'actual_type': file_type
            })
            # Don't reject, but log as suspicious
        
        # Calculate file hash for integrity
        file_hash = self._calculate_file_hash(file_path)
        
        validation_result = {
            'size': file_size,
            'type': file_type,
            'signature': file_signature,
            'hash': file_hash,
            'extension': file_ext,
            'is_valid': True
        }
        
        logger.info("File validated successfully", extra={
            'filename': file_path.name,
            'size': file_size,
            'type': file_type
        })
        
        return validation_result
    
    def _check_dangerous_patterns(self, text: str, context: str = "input"):
        """Check for dangerous patterns in text"""
        for pattern in self.compiled_dangerous_patterns:
            if pattern.search(text):
                log_security_event("dangerous_pattern_detected", {
                    'context': context,
                    'pattern': pattern.pattern,
                    'text_sample': text[:100]
                })
                raise SecurityError(f"Dangerous pattern detected in {context}")
    
    def _check_sql_injection(self, text: str):
        """Check for SQL injection patterns"""
        for pattern in self.compiled_sql_patterns:
            if pattern.search(text):
                log_security_event("sql_injection_attempt", {
                    'pattern': pattern.pattern,
                    'text_sample': text[:100]
                })
                raise SecurityError("Potential SQL injection detected")
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text input"""
        # Remove null bytes
        text = text.replace('\0', '')
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Strip dangerous Unicode characters
        text = ''.join(char for char in text if ord(char) < 65536)
        
        return text.strip()
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

class RateLimiter:
    """Simple rate limiter for production use"""
    
    def __init__(self):
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, identifier: str, max_requests: int = None, 
                   window_seconds: int = 60) -> bool:
        """Check if request is allowed under rate limit"""
        import time
        
        max_requests = max_requests or config.RATE_LIMIT_PER_MINUTE
        current_time = time.time()
        
        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if current_time - req_time < window_seconds
            ]
        else:
            self.requests[identifier] = []
        
        # Check limit
        if len(self.requests[identifier]) >= max_requests:
            log_security_event("rate_limit_exceeded", {
                'identifier': identifier,
                'requests_count': len(self.requests[identifier]),
                'max_requests': max_requests
            })
            return False
        
        # Add current request
        self.requests[identifier].append(current_time)
        return True

# Global instances
validator = InputValidator()
rate_limiter = RateLimiter()

# Convenience functions
def validate_query(query: str) -> str:
    return validator.validate_query(query)

def validate_filename(filename: str) -> str:
    return validator.validate_filename(filename)

def validate_file_content(file_path: Path, max_size: int = None) -> Dict[str, Any]:
    return validator.validate_file_content(file_path, max_size)

def check_rate_limit(identifier: str) -> bool:
    return rate_limiter.is_allowed(identifier)