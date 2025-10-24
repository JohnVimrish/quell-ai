
# Empty file to make it a package
from .feed_controller import bp as feed_bp
from .copilot_controller import bp as copilot_bp
# Archived (Oct 2025): contacts_controller, calls_controller moved to backend/archive
# from .contacts_controller import bp as contacts_bp
# from .calls_controller import bp as calls_bp
from .texts_controller import bp as texts_bp
# Archived (Oct 2025): report_controller, status_controller moved to backend/archive
# from .report_controller import bp as report_bp
# from .status_controller import bp as status_bp
from .webhooks_controller import bp as webhooks_bp
from .auth_controller import bp as auth_bp
from .labs_controller import bp as labs_bp

__all__ = [
    'feed_bp',
    'copilot_bp', 
    # 'contacts_bp',
    # 'calls_bp',
    'texts_bp',
    # 'report_bp',
    'webhooks_bp',
    'auth_bp',
    # 'status_bp',
    'labs_bp'
]
