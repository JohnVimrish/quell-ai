
import logging
import logging.handlers
import json
import time
import socket
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
    
    def configure(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Configure logging with the provided configuration."""
        try:
            self._config = config or {}
            self._validate_config()
            self._reset_logging()
            self._configure_levels()
            self._configure_console_logging()
            self._configure_graylog()
            self._configure_squelching()
            self._is_configured = True
            
            # Log successful configuration
            logger = self.get_logger("logging.manager")
            sanitized_config = self._sanitize_config_for_logging()
            logger.info("Logging configured successfully", extra={"config": sanitized_config})
            
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
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on logging system."""
        health = {
            "configured": self._is_configured,
            "graylog_available": False,
            "handlers_count": len(logging.getLogger().handlers)
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
