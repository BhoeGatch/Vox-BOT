"""Production configuration management"""
import os
from pathlib import Path
from typing import Dict, Any

class Config:
    """Production-ready configuration class"""
    
    # File handling settings
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 50 * 1024 * 1024))  # 50MB default
    ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt'}
    MAX_FILES_PER_SESSION = int(os.getenv('MAX_FILES_PER_SESSION', 10))
    
    # Search engine settings
    SEARCH_MAX_RESULTS = int(os.getenv('SEARCH_MAX_RESULTS', 5))
    SEARCH_TIMEOUT = int(os.getenv('SEARCH_TIMEOUT', 30))  # seconds
    MIN_QUERY_LENGTH = int(os.getenv('MIN_QUERY_LENGTH', 3))
    MAX_QUERY_LENGTH = int(os.getenv('MAX_QUERY_LENGTH', 500))
    
    # Text processing settings
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 1500))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 200))
    MIN_CHUNK_SIZE = int(os.getenv('MIN_CHUNK_SIZE', 50))
    
    # Application settings
    APP_NAME = os.getenv('APP_NAME', 'WNS Vox BOT')
    APP_VERSION = os.getenv('APP_VERSION', '2.0.0')
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    
    # Directories
    DATA_DIR = Path(os.getenv('DATA_DIR', 'data'))
    LOGS_DIR = Path(os.getenv('LOGS_DIR', 'logs'))
    TEMP_DIR = Path(os.getenv('TEMP_DIR', 'temp'))
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')  # json or text
    LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', 30))
    
    # Security settings
    ENABLE_FILE_SCAN = os.getenv('ENABLE_FILE_SCAN', 'true').lower() == 'true'
    MAX_CONCURRENT_USERS = int(os.getenv('MAX_CONCURRENT_USERS', 100))
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 60))
    
    # Performance settings
    CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))  # 1 hour
    ENABLE_CACHING = os.getenv('ENABLE_CACHING', 'true').lower() == 'true'
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories"""
        for directory in [cls.DATA_DIR, cls.LOGS_DIR, cls.TEMP_DIR]:
            directory.mkdir(exist_ok=True, parents=True)
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """Get configuration as dictionary for logging"""
        return {
            'app_name': cls.APP_NAME,
            'app_version': cls.APP_VERSION,
            'debug_mode': cls.DEBUG_MODE,
            'max_file_size': cls.MAX_FILE_SIZE,
            'allowed_extensions': list(cls.ALLOWED_EXTENSIONS),
            'search_timeout': cls.SEARCH_TIMEOUT,
            'log_level': cls.LOG_LEVEL
        }

# Global config instance
config = Config()