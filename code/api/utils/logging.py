
import logging
import logging.handlers
import json
import time
import socket
import os
import glob
from typing import Any, Dict, Optional, Union
from datetime import datetime

# Reserved logging fields
RESERVED_FIELDS = {
    "name", "msg", "args", "levelname", "levelno", "pathname",
    "filename", "module", "exc_info", "exc_text", "stack_info",
    "lineno", "funcName", "created", "msecs", "relativeCreated",
    "thread", "threadName", "processName", "process", "getMessage"
}

class LoggingError(Exception):
    """Custom exception for logging-related errors."""
    pass


class TimestampedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    A rotating file handler that creates timestamped log files.
    
    Features:
    - Creates a new log file with timestamp on startup
    - Handles rollovers with iteration numbers
    - Format: service_name_YYYYMMDD_HHMMSS_N.log
    - Where N is the iteration number (0, 1, 2, etc.)
    """
    
    def __init__(self, filename, maxBytes=0, backupCount=0, encoding=None, delay=False):
        """
        Initialize the timestamped rotating file handler.
        
        Args:
            filename: Base filename pattern (without extension)
            maxBytes: Maximum file size before rotation (0 = no limit)
            backupCount: Number of backup files to keep
            encoding: File encoding
            delay: Whether to delay file creation until first write
        """
        self.base_filename = filename
        self.maxBytes = maxBytes
        self.backupCount = backupCount
        self.encoding = encoding
        self.delay = delay
        
        # Generate initial timestamped filename
        self.current_filename = self._generate_filename()
        
        # Initialize parent with the timestamped filename
        super().__init__(
            self.current_filename,
            maxBytes=maxBytes,
            backupCount=backupCount,
            encoding=encoding,
            delay=delay
        )
    
    def _generate_filename(self, iteration=0):
        """
        Generate a timestamped filename with iteration number.
        
        Args:
            iteration: Iteration number for rollovers
            
        Returns:
            str: Generated filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if iteration == 0:
            return f"{self.base_filename}_{timestamp}.log"
        else:
            return f"{self.base_filename}_{timestamp}_{iteration}.log"
    
    def _get_next_iteration(self):
        """
        Get the next iteration number for rollover.
        
        Returns:
            int: Next iteration number
        """
        # Extract timestamp from current filename
        base_name = os.path.splitext(self.current_filename)[0]
        timestamp_part = base_name.split('_')[-2] + '_' + base_name.split('_')[-1]
        
        # Find all existing files with the same timestamp
        pattern = f"{self.base_filename}_{timestamp_part}_*.log"
        existing_files = glob.glob(os.path.join(os.path.dirname(self.current_filename), pattern))
        
        # Find the highest iteration number
        max_iteration = -1
        for file_path in existing_files:
            filename = os.path.basename(file_path)
            parts = filename.split('_')
            if len(parts) >= 4:  # base_timestamp_iteration.log
                try:
                    iteration = int(parts[-2])
                    max_iteration = max(max_iteration, iteration)
                except (ValueError, IndexError):
                    continue
        
        return max_iteration + 1
    
    def doRollover(self):
        """
        Perform rollover when file size limit is reached.
        Creates a new file with incremented iteration number.
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        
        # Generate new filename with incremented iteration
        next_iteration = self._get_next_iteration()
        new_filename = self._generate_filename(next_iteration)
        
        # Update current filename
        self.current_filename = new_filename
        
        # Clean up old files if backupCount is set
        if self.backupCount > 0:
            self._cleanup_old_files()
        
        # Open new file
        if not self.delay:
            self.stream = self._open()
    
    def _cleanup_old_files(self):
        """
        Clean up old log files based on backupCount.
        Keeps the most recent files and removes older ones.
        """
        try:
            # Get all log files for this service
            log_dir = os.path.dirname(self.current_filename)
            pattern = f"{self.base_filename}_*.log"
            all_files = glob.glob(os.path.join(log_dir, pattern))
            
            # Sort by modification time (newest first)
            all_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Remove files beyond backupCount
            files_to_remove = all_files[self.backupCount:]
            for file_path in files_to_remove:
                try:
                    os.remove(file_path)
                except OSError:
                    pass  # Ignore errors when removing files
                    
        except Exception:
            pass  # Ignore cleanup errors
    
    def emit(self, record):
        """
        Emit a log record.
        Override to ensure we're using the current filename.
        """
        try:
            if self.shouldRollover(record):
                self.doRollover()
            
            super().emit(record)
        except Exception:
            self.handleError(record)


class RequestContextFilter(logging.Filter):
    """
    A logging filter that injects Flask request context information into log records.
    
    This filter enhances log records with request-specific information when running
    within a Flask application context, including:
    - Request ID for tracing
    - HTTP method and path
    - Client IP address (with proxy support)
    - User agent string
    
    When no Flask context is available, empty values are provided to maintain
    consistent log structure.
    """
    
    def __init__(self):
        """Initialize the request context filter."""
        super().__init__()
        self._default_attrs = {
            "request_id": "",
            "method": "",
            "path": "",
            "remote_addr": "",
            "user_agent": ""
        }
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter method that adds request context to log records.
        
        Args:
            record: The log record to enhance
            
        Returns:
            bool: Always True to allow the record to be processed
        """
        try:
            if FLASK_AVAILABLE and has_request_context():
                self._add_flask_context(record)
            else:
                self._add_default_context(record)
        except Exception as e:
            # Never break logging - add default context and continue
            self._add_default_context(record)
            # Optionally log the error (but avoid infinite recursion)
            if hasattr(record, '_context_error_logged'):
                return True
            record._context_error_logged = True
            
        return True
    
    def _add_flask_context(self, record: logging.LogRecord) -> None:
        """Add Flask request context information to the log record."""
        try:
            # Request ID from Flask's g object
            setattr(record, "request_id", getattr(g, "request_id", ""))
            
            # HTTP method and path
            setattr(record, "method", getattr(request, "method", ""))
            setattr(record, "path", getattr(request, "path", ""))
            
            # Client IP with proxy support
            remote_addr = self._get_client_ip()
            setattr(record, "remote_addr", remote_addr)
            
            # User agent
            user_agent = self._get_user_agent()
            setattr(record, "user_agent", user_agent)
            
        except Exception:
            # Fallback to default context
            self._add_default_context(record)
    
    def _add_default_context(self, record: logging.LogRecord) -> None:
        """Add default empty context when Flask context is unavailable."""
        for attr, default_value in self._default_attrs.items():
            setattr(record, attr, default_value)
    
    def _get_client_ip(self) -> str:
        """
        Extract client IP address with support for proxy headers.
        
        Returns:
            str: Client IP address or empty string if unavailable
        """
        try:
            if not request:
                return ""
            
            # Check for proxy headers first
            forwarded_for = request.headers.get("X-Forwarded-For", "").strip()
            if forwarded_for:
                # Take the first IP in case of multiple proxies
                return forwarded_for.split(",")[0].strip()
            
            # Check other common proxy headers
            real_ip = request.headers.get("X-Real-IP", "").strip()
            if real_ip:
                return real_ip
            
            # Fallback to direct connection
            return getattr(request, "remote_addr", "") or ""
            
        except Exception:
            return ""
    
    def _get_user_agent(self) -> str:
        """
        Extract user agent string from request.
        
        Returns:
            str: User agent string or empty string if unavailable
        """
        try:
            if not request:
                return ""
            
            user_agent = getattr(request, "user_agent", None)
            return str(user_agent) if user_agent else ""
            
        except Exception:
            return ""


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def __init__(self, static_fields: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.static_fields = static_fields or {}
        self._validate_static_fields()
    
    def _validate_static_fields(self) -> None:
        """Validate that static fields are JSON serializable."""
        try:
            json.dumps(self.static_fields)
        except (TypeError, ValueError) as e:
            raise LoggingError(f"Static fields are not JSON serializable: {e}")
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        try:
            # Build base log structure
            log_entry = self._build_base_entry(record)
            
            # Add static fields
            log_entry.update(self.static_fields)
            
            # Add dynamic fields from record
            self._add_dynamic_fields(log_entry, record)
            
            # Add exception information if present
            self._add_exception_info(log_entry, record)
            
            return json.dumps(log_entry, ensure_ascii=False, default=str)
            
        except Exception as e:
            # Fallback to basic string representation
            return self._create_fallback_entry(record, str(e))
    
    def _build_base_entry(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Build the base log entry structure."""
        return {
            "timestamp": datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", ""),
            "method": getattr(record, "method", ""),
            "path": getattr(record, "path", ""),
            "remote_addr": getattr(record, "remote_addr", ""),
            "user_agent": getattr(record, "user_agent", ""),
        }
    
    def _add_dynamic_fields(self, log_entry: Dict[str, Any], record: logging.LogRecord) -> None:
        """Add dynamic fields from the log record."""
        for key, value in record.__dict__.items():
            if key in RESERVED_FIELDS or key in log_entry:
                continue
            
            try:
                # Test JSON serializability
                json.dumps(value)
                log_entry[key] = value
            except (TypeError, ValueError):
                # Convert non-serializable values to strings
                log_entry[key] = str(value)
    
    def _add_exception_info(self, log_entry: Dict[str, Any], record: logging.LogRecord) -> None:
        """Add exception information if present in the record."""
        if record.exc_info:
            try:
                log_entry["exception"] = self.formatException(record.exc_info)
            except Exception:
                log_entry["exception"] = "Failed to format exception"
    
    def _create_fallback_entry(self, record: logging.LogRecord, error: str) -> str:
        """Create a fallback log entry when JSON formatting fails."""
        fallback = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": "ERROR",
            "logger": "logging.formatter",
            "message": f"Failed to format log record: {error}",
            "original_message": getattr(record, "message", str(record.msg)),
            "original_level": record.levelname
        }
        return json.dumps(fallback, ensure_ascii=False)


class GraylogHandler:
    """A wrapper class for Graylog (GELF) handler with enhanced error handling."""
    
    def __init__(self, host: str, port: int, facility: str = "python"):
        self.host = host
        self.port = port
        self.facility = facility
        self._handler = None
        self._is_available = False
        self._last_check = 0
        self._check_interval = 300  # 5 minutes
    
    def create_handler(self) -> Optional[logging.Handler]:
        """Create and return a Graylog handler if available."""
        try:
            if self._test_connection():
                # Try to import graypy (install with: pip install graypy)
                try:
                    import graypy
                    self._handler = graypy.GELFUDPHandler(
                        self.host, 
                        self.port,
                        facility=self.facility
                    )
                    self._is_available = True
                    return self._handler
                except ImportError:
                    # Fallback to basic UDP handler if graypy not available
                    self._handler = logging.handlers.DatagramHandler(self.host, self.port)
                    self._is_available = True
                    return self._handler
            else:
                self._is_available = False
                return None
        except Exception as e:
            logging.getLogger("logging.graylog").warning(f"Failed to create Graylog handler: {e}")
            self._is_available = False
            return None
    
    def _test_connection(self) -> bool:
        """Test if Graylog server is reachable."""
        current_time = time.time()
        if current_time - self._last_check < self._check_interval and self._is_available:
            return True
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            sock.connect((self.host, self.port))
            sock.close()
            self._last_check = current_time
            return True
        except Exception:
            self._last_check = current_time
            return False
    
    def is_healthy(self) -> bool:
        """Check if Graylog handler is healthy."""
        return self._is_available


class LoggerManager:
    """Central manager for logging configuration and Graylog integration."""
    
    def __init__(self):
        self._loggers: Dict[str, logging.Logger] = {}
        self._graylog_handler: Optional[GraylogHandler] = None
        self._is_configured = False
        self._config: Dict[str, Any] = {}
    

    def _configure_file_logging(self) -> None:
        """Configure file logging with timestamped rotation"""
        try:
            # Get log directory from config or use default
            log_dir = self._config.get("log_directory", "logs")
            
            # Create absolute path
            if not os.path.isabs(log_dir):
                # Create logs directory relative to project root
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                log_dir = os.path.join(project_root, log_dir)
            
            os.makedirs(log_dir, exist_ok=True)
            
            # Create base log filename (without extension)
            service_name = self._config.get("service_name", "quell-ai")
            log_base_filename = os.path.join(log_dir, service_name)
            
            # Get configuration for file logging
            max_bytes = self._config.get("log_max_bytes", 10 * 1024 * 1024)  # 10MB default
            backup_count = self._config.get("log_backup_count", 5)  # Keep 5 files default
            
            # Create timestamped rotating file handler
            file_handler = TimestampedRotatingFileHandler(
                log_base_filename,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            
            # Set level
            level = getattr(logging, self._config.get("level", "INFO").upper())
            file_handler.setLevel(level)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(formatter)
            
            # Add to root logger
            logging.getLogger().addHandler(file_handler)
            
            # Log the configuration
            print(f"Timestamped file logging configured: {file_handler.current_filename}")
            print(f"Max file size: {max_bytes} bytes, Backup count: {backup_count}")
            
        except Exception as e:
            print(f"Failed to configure file logging: {e}")

    def configure(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Configure logging with console and file output"""
        try:
            self._config = config or {}
            self._validate_config()
            self._reset_logging()
            self._configure_levels()
            self._configure_console_logging()
            self._configure_file_logging()  # Add this line
            
            if self._config.get("graylog"):
                self._configure_graylog()
            
            self._configure_squelching()
            self._is_configured = True
            
            # Log configuration summary
            sanitized = self._sanitize_config_for_logging()
            logging.info(f"Logging configured: {sanitized}")
            
        except Exception as e:
            raise LoggingError(f"Failed to configure logging: {e}")
    
    def _validate_config(self) -> None:
        """Validate the logging configuration."""
        if not isinstance(self._config, dict):
            raise LoggingError("Configuration must be a dictionary")
        
        # Validate log level
        level = self._config.get("level", "INFO")
        if not hasattr(logging, level.upper()):
            raise LoggingError(f"Invalid log level: {level}")
        
        # Validate Graylog config if present
        graylog_config = self._config.get("graylog")
        if graylog_config:
            if not isinstance(graylog_config, dict):
                raise LoggingError("Graylog configuration must be a dictionary")
            
            required_fields = ["host", "port"]
            for field in required_fields:
                if field not in graylog_config:
                    raise LoggingError(f"Missing required Graylog field: {field}")
    
    def _reset_logging(self) -> None:
        """Reset logging configuration."""
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        root_logger.setLevel(logging.NOTSET)
    
    def _configure_levels(self) -> None:
        """Configure logging levels."""
        level = getattr(logging, self._config.get("level", "INFO").upper())
        logging.getLogger().setLevel(level)
    
    def _configure_console_logging(self) -> None:
        """Configure console logging."""
        console_handler = logging.StreamHandler()
        
        # Use JSON formatter if specified, otherwise use standard formatter
        if self._config.get("format") == "json":
            static_fields = {"service": self._config.get("service_name", "unknown")}
            formatter = JSONFormatter(static_fields=static_fields)
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)
    
    def _configure_graylog(self) -> None:
        """Configure Graylog integration if specified."""
        graylog_config = self._config.get("graylog")
        if not graylog_config:
            return
        
        try:
            self._graylog_handler = GraylogHandler(
                host=graylog_config["host"],
                port=graylog_config["port"],
                facility=graylog_config.get("facility", "python")
            )
            
            graylog_handler = self._graylog_handler.create_handler()
            if graylog_handler:
                # Use JSON formatter for Graylog
                static_fields = {"service": self._config.get("service_name", "unknown")}
                formatter = JSONFormatter(static_fields=static_fields)
                graylog_handler.setFormatter(formatter)
                
                # Add to root logger
                logging.getLogger().addHandler(graylog_handler)
                
        except Exception as e:
            logging.getLogger("logging.manager").warning(
                f"Failed to configure Graylog: {e}"
            )
    
    def _configure_squelching(self) -> None:
        """Configure log level squelching for noisy loggers."""
        squelch_loggers = self._config.get("squelch", [])
        for logger_name in squelch_loggers:
            logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    def _sanitize_config_for_logging(self) -> Dict[str, Any]:
        """Sanitize config for logging (remove sensitive data)."""
        sanitized = self._config.copy()
        if "graylog" in sanitized:
            graylog = sanitized["graylog"].copy()
            # Don't log sensitive connection details
            graylog.pop("password", None)
            sanitized["graylog"] = graylog
        return sanitized
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger with the given name."""
        if name not in self._loggers:
            logger = logging.getLogger(name)
            logger.addFilter(RequestContextFilter())
            self._loggers[name] = logger
        return self._loggers[name]
    
    def is_configured(self) -> bool:
        """Check if logging is configured."""
        return self._is_configured
    
    def get_current_log_file(self) -> Optional[str]:
        """Get the current active log file path."""
        try:
            for handler in logging.getLogger().handlers:
                if isinstance(handler, TimestampedRotatingFileHandler):
                    return handler.current_filename
        except Exception:
            pass
        return None
    
    def get_log_files_info(self) -> Dict[str, Any]:
        """Get information about all log files."""
        try:
            log_dir = self._config.get("log_directory", "logs")
            if not os.path.isabs(log_dir):
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                log_dir = os.path.join(project_root, log_dir)
            
            service_name = self._config.get("service_name", "quell-ai")
            pattern = f"{service_name}_*.log"
            log_files = glob.glob(os.path.join(log_dir, pattern))
            
            # Sort by modification time (newest first)
            log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            files_info = []
            for file_path in log_files:
                try:
                    stat = os.stat(file_path)
                    files_info.append({
                        "filename": os.path.basename(file_path),
                        "path": file_path,
                        "size_bytes": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "is_current": file_path == self.get_current_log_file()
                    })
                except OSError:
                    continue
            
            return {
                "log_directory": log_dir,
                "service_name": service_name,
                "total_files": len(files_info),
                "files": files_info
            }
        except Exception as e:
            return {"error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on logging system."""
        health = {
            "configured": self._is_configured,
            "graylog_available": False,
            "handlers_count": len(logging.getLogger().handlers),
            "current_log_file": self.get_current_log_file(),
            "log_files_info": self.get_log_files_info()
        }
        
        if self._graylog_handler:
            health["graylog_available"] = self._graylog_handler.is_healthy()
        
        return health

# Optional Flask imports with graceful fallback
try:
    from flask import has_request_context, request, g
    FLASK_AVAILABLE = True
except ImportError:
    # Graceful fallback when Flask is not available
    FLASK_AVAILABLE = False
    has_request_context = lambda: False
    request = None
    g = object()


# Global logger manager instance
logger_manager = LoggerManager()

def configure_logging(config: Dict[str, Any]) -> None:
    """Configure logging using the global logger manager."""
    logger_manager.configure(config)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logger_manager.get_logger(name)

def get_current_log_file() -> Optional[str]:
    """Get the current active log file path."""
    return logger_manager.get_current_log_file()

def get_log_files_info() -> Dict[str, Any]:
    """Get information about all log files."""
    return logger_manager.get_log_files_info()

def get_logging_health() -> Dict[str, Any]:
    """Get logging system health information."""
    return logger_manager.health_check()
