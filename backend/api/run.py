
import os
import sys
import logging
import signal
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from api.app import create_app
from api.utils.config import Config

# Configure logging for startup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_signal_handlers(app):
    """Setup graceful shutdown signal handlers"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        
        # Cleanup tasks
        try:
            # Close database connections
            if hasattr(app, 'config') and app.config.get('DB_MANAGER'):
                app.config['DB_MANAGER'].close_all_connections()
                logger.info("Database connections closed")
            
            # Cleanup AI models
            if hasattr(app, 'config'):
                spam_detector = app.config.get('SPAM_DETECTOR')
                rag_system = app.config.get('RAG_SYSTEM')
                
                if spam_detector:
                    spam_detector.cleanup()
                    logger.info("Spam detector cleaned up")
                
                if rag_system:
                    rag_system.cleanup()
                    logger.info("RAG system cleaned up")
            
            logger.info("Graceful shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def validate_environment():
    """Validate required environment variables and configuration"""
    required_vars = [
        # DATABASE_URL is enforced via code/api/.env (loaded by Config), not from process env
        'SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file or environment configuration")
        return False
    
    # Validate optional but recommended variables
    optional_vars = [
        'TWILIO_ACCOUNT_SID',
        'TWILIO_AUTH_TOKEN',
        'DEEPGRAM_API_KEY',
        'ELEVENLABS_API_KEY',
        'OPENAI_API_KEY'
    ]
    
    missing_optional = []
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
    
    if missing_optional:
        logger.warning(f"Optional environment variables not set: {', '.join(missing_optional)}")
        logger.warning("Some features may not be available")
    
    return True

def create_directories():
    """Create necessary directories for the application"""
    directories = [
        'models',
        'voice_samples',
        'transcripts',
        'logs',
        'uploads',
        'temp'
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(exist_ok=True)
        logger.info(f"Ensured directory exists: {dir_path}")

def main():
    """Main application entry point"""
    try:
        logger.info("Starting Communicator-Copilot application...")
        
        # Validate environment
        if not validate_environment():
            sys.exit(1)
        
        # Create necessary directories
        create_directories()
        
        # Load configuration
        try:
            config = Config.load()
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            sys.exit(1)
        
        # Create Flask application
        try:
            app = create_app(config)
            logger.info("Flask application created successfully")
        except Exception as e:
            logger.error(f"Failed to create Flask application: {e}")
            sys.exit(1)
        
        # Setup signal handlers for graceful shutdown
        setup_signal_handlers(app)
        
        # Get configuration from environment
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 8080))
        debug = config.debug
        
        logger.info(f"Starting server on {host}:{port} (debug={debug})")
        
        # Run the application
        if debug:
            # Development mode with Flask's built-in server
            app.run(
                host=host,
                port=port,
                debug=debug,
                threaded=True,
                use_reloader=False  # Disable reloader to avoid signal handler conflicts
            )
        else:
            # Production mode - recommend using gunicorn or uvicorn
            logger.info("Running in production mode")
            logger.info("For production deployment, consider using:")
            logger.info(f"  gunicorn -w 4 -b {host}:{port} api.app:create_app()")
            logger.info(f"  or uvicorn api.app:create_app --host {host} --port {port}")
            
            # Fallback to Flask's built-in server
            app.run(
                host=host,
                port=port,
                debug=False,
                threaded=True
            )
            
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
