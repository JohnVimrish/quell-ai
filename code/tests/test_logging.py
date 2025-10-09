#!/usr/bin/env python3
"""
Test script for the new timestamped logging system
"""
import sys
import os
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.utils.logging import configure_logging, get_logger, get_current_log_file, get_log_files_info, get_logging_health

def test_timestamped_logging():
    """Test the timestamped logging functionality"""
    
    # Configure logging
    config = {
        "level": "INFO",
        "service_name": "quell-ai-test",
        "log_directory": "logs",
        "log_max_bytes": 1024,  # 1KB for testing rollover
        "log_backup_count": 3
    }
    
    print("🚀 Configuring timestamped logging...")
    configure_logging(config)
    
    # Get logger
    logger = get_logger("test_logging")
    
    # Log some messages
    print("📝 Writing test log messages...")
    logger.info("Application started")
    logger.info("This is a test message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Show current log file
    current_file = get_current_log_file()
    print(f"📄 Current log file: {current_file}")
    
    # Show log files info
    print("\n📊 Log files information:")
    files_info = get_log_files_info()
    print(f"Log directory: {files_info.get('log_directory')}")
    print(f"Service name: {files_info.get('service_name')}")
    print(f"Total files: {files_info.get('total_files')}")
    
    for file_info in files_info.get('files', []):
        status = "🟢 CURRENT" if file_info['is_current'] else "📄"
        print(f"  {status} {file_info['filename']} ({file_info['size_mb']} MB)")
    
    # Test rollover by writing many messages
    print("\n🔄 Testing rollover (writing many messages to trigger size limit)...")
    for i in range(50):
        logger.info(f"Test message {i+1} - This is a longer message to help trigger rollover")
        time.sleep(0.01)  # Small delay
    
    # Show updated log files info
    print("\n📊 Updated log files information after rollover:")
    files_info = get_log_files_info()
    for file_info in files_info.get('files', []):
        status = "🟢 CURRENT" if file_info['is_current'] else "📄"
        print(f"  {status} {file_info['filename']} ({file_info['size_mb']} MB)")
    
    # Show health check
    print("\n🏥 Logging system health:")
    health = get_logging_health()
    print(f"Configured: {health['configured']}")
    print(f"Handlers count: {health['handlers_count']}")
    print(f"Current log file: {health['current_log_file']}")
    
    print("\n✅ Timestamped logging test completed!")

if __name__ == "__main__":
    test_timestamped_logging()
