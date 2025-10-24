Archived backend modules (October 2025)

Reason: Temporarily paused feature implementation for code organization and maintainability. These modules are preserved for potential future reactivation.

Archived items and original paths:

- api/controllers/calls_controller.py -> backend/archive/api/controllers/calls_controller.py
- api/controllers/contacts_controller.py -> backend/archive/api/controllers/contacts_controller.py
- api/controllers/report_controller.py -> backend/archive/api/controllers/report_controller.py
- api/controllers/status_controller.py -> backend/archive/api/controllers/status_controller.py
- api/models/spam_detector.py -> backend/archive/api/models/spam_detector.py

Runtime notes:

- Blueprint registrations for calls, contacts, and reports have been commented out in `backend/api/app.py` to avoid import/runtime errors.
- `SpamDetector` import and initialization are now optional in `backend/api/app.py` and `backend/api/controllers/copilot_controller.py`. When unavailable, spam analysis is skipped gracefully.
- Package imports in `backend/api/controllers/__init__.py` have been adjusted to exclude archived modules.

To restore:

- Move files back to their original paths listed above.
- Re-enable imports and `app.register_blueprint` lines in `backend/api/app.py`.
- Restore imports in `backend/api/controllers/__init__.py`.
