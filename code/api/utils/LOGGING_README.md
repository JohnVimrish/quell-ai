# Timestamped Logging System

This document describes the new timestamped logging system for Quell-Ai that creates timestamped log files on startup and handles rollovers with iteration numbers.

## Features

### 🕒 **Timestamped Files**
- Creates a new log file with timestamp every time the application starts
- Format: `service_name_YYYYMMDD_HHMMSS.log`
- Example: `quell-ai_20240923_143052.log`

### 🔄 **Smart Rollover**
- When log file reaches size limit, creates new file with iteration number
- Format: `service_name_YYYYMMDD_HHMMSS_N.log`
- Example: `quell-ai_20240923_143052_1.log`, `quell-ai_20240923_143052_2.log`

### 🧹 **Automatic Cleanup**
- Keeps only the specified number of backup files
- Removes oldest files when limit is exceeded
- Configurable backup count

## Configuration

### Basic Configuration
```python
from api.utils.logging import configure_logging

config = {
    "level": "INFO",
    "service_name": "quell-ai",
    "log_directory": "logs",
    "log_max_bytes": 10 * 1024 * 1024,  # 10MB
    "log_backup_count": 5
}

configure_logging(config)
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `level` | str | "INFO" | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `service_name` | str | "quell-ai" | Base name for log files |
| `log_directory` | str | "logs" | Directory to store log files |
| `log_max_bytes` | int | 10MB | Maximum file size before rollover |
| `log_backup_count` | int | 5 | Number of backup files to keep |
| `format` | str | "text" | Log format ("text" or "json") |

## Usage Examples

### Basic Usage
```python
from api.utils.logging import get_logger

logger = get_logger("my_module")
logger.info("Application started")
logger.warning("This is a warning")
logger.error("An error occurred")
```

### Get Current Log File
```python
from api.utils.logging import get_current_log_file

current_file = get_current_log_file()
print(f"Current log file: {current_file}")
```

### Get All Log Files Information
```python
from api.utils.logging import get_log_files_info

files_info = get_log_files_info()
print(f"Total log files: {files_info['total_files']}")

for file_info in files_info['files']:
    status = "CURRENT" if file_info['is_current'] else "BACKUP"
    print(f"{status}: {file_info['filename']} ({file_info['size_mb']} MB)")
```

### Health Check
```python
from api.utils.logging import get_logging_health

health = get_logging_health()
print(f"Logging configured: {health['configured']}")
print(f"Current log file: {health['current_log_file']}")
```

## File Naming Convention

### Startup Files
- **Format**: `service_name_YYYYMMDD_HHMMSS.log`
- **Example**: `quell-ai_20240923_143052.log`
- **Created**: When application starts

### Rollover Files
- **Format**: `service_name_YYYYMMDD_HHMMSS_N.log`
- **Example**: `quell-ai_20240923_143052_1.log`
- **Created**: When file size limit is reached

### Examples
```
logs/
├── quell-ai_20240923_143052.log      # Initial file
├── quell-ai_20240923_143052_1.log    # First rollover
├── quell-ai_20240923_143052_2.log    # Second rollover
├── quell-ai_20240923_143052_3.log    # Third rollover
└── quell-ai_20240923_143052_4.log    # Fourth rollover (current)
```

## Log File Management

### Automatic Cleanup
- Oldest files are automatically removed when `backup_count` is exceeded
- Files are sorted by modification time (newest first)
- Only files matching the service name pattern are considered

### Manual Cleanup
```python
import os
import glob

# Get all log files for a service
log_dir = "logs"
service_name = "quell-ai"
pattern = f"{service_name}_*.log"
log_files = glob.glob(os.path.join(log_dir, pattern))

# Sort by modification time (oldest first)
log_files.sort(key=lambda x: os.path.getmtime(x))

# Remove old files (keep last 5)
files_to_remove = log_files[:-5]
for file_path in files_to_remove:
    os.remove(file_path)
```

## Testing

### Run Test Script
```bash
python code/api/test_logging.py
```

### Test Output
```
🚀 Configuring timestamped logging...
📝 Writing test log messages...
📄 Current log file: logs/quell-ai-test_20240923_143052.log
📊 Log files information:
Log directory: logs
Service name: quell-ai-test
Total files: 1
  🟢 CURRENT quell-ai-test_20240923_143052.log (0.01 MB)

🔄 Testing rollover (writing many messages to trigger size limit)...
📊 Updated log files information after rollover:
  📄 quell-ai-test_20240923_143052.log (0.00 MB)
  🟢 CURRENT quell-ai-test_20240923_143052_1.log (0.01 MB)

🏥 Logging system health:
Configured: True
Handlers count: 2
Current log file: logs/quell-ai-test_20240923_143052_1.log

✅ Timestamped logging test completed!
```

## Integration with Flask

### In your Flask app
```python
from flask import Flask
from api.utils.logging import configure_logging, get_logger

app = Flask(__name__)

# Configure logging
configure_logging({
    "level": "INFO",
    "service_name": "quell-ai",
    "log_directory": "logs",
    "log_max_bytes": 10 * 1024 * 1024,
    "log_backup_count": 5
})

# Get logger
logger = get_logger(__name__)

@app.route('/')
def home():
    logger.info("Home page accessed")
    return "Hello World"
```

## Advanced Features

### JSON Logging
```python
config = {
    "level": "INFO",
    "format": "json",
    "service_name": "quell-ai"
}
configure_logging(config)
```

### Graylog Integration
```python
config = {
    "level": "INFO",
    "service_name": "quell-ai",
    "graylog": {
        "host": "graylog.example.com",
        "port": 12201,
        "facility": "quell-ai"
    }
}
configure_logging(config)
```

### Custom Formatters
```python
from api.utils.logging import JSONFormatter

# Custom JSON formatter with static fields
formatter = JSONFormatter(static_fields={
    "environment": "production",
    "version": "1.0.0"
})
```

## Troubleshooting

### Common Issues

1. **Permission Errors**
   - Ensure the log directory is writable
   - Check file permissions

2. **Disk Space**
   - Monitor log directory size
   - Adjust `log_max_bytes` and `log_backup_count`

3. **File Locking**
   - Avoid multiple processes writing to same log file
   - Use separate service names for different processes

### Debug Mode
```python
config = {
    "level": "DEBUG",
    "service_name": "quell-ai-debug"
}
configure_logging(config)
```

## Migration from Old System

### Before (Old System)
```
logs/
├── quell-ai.log
├── quell-ai.log.1
├── quell-ai.log.2
└── quell-ai.log.3
```

### After (New System)
```
logs/
├── quell-ai_20240923_143052.log
├── quell-ai_20240923_143052_1.log
├── quell-ai_20240923_143052_2.log
└── quell-ai_20240923_143052_3.log
```

### Benefits
- **Better Organization**: Timestamped files are easier to identify
- **No Conflicts**: Each startup gets a unique timestamp
- **Clear History**: Easy to see when files were created
- **Rollover Clarity**: Iteration numbers show rollover sequence



