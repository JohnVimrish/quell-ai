Archived frontend routes/components (October 2025)

Reason: Temporarily paused feature implementation aligned with backend archiving. Components preserved for future reactivation.

Archived items and original paths:

- src/pages/CallsPage.tsx -> frontend/archive/src/pages/CallsPage.tsx
- src/pages/ContactsPage.tsx -> frontend/archive/src/pages/ContactsPage.tsx
- src/pages/ReportsPage.tsx -> frontend/archive/src/pages/ReportsPage.tsx
- legacy/templates/calls.html -> frontend/archive/legacy/templates/calls.html
- legacy/templates/reports.html -> frontend/archive/legacy/templates/reports.html

Runtime notes:

- Routes and lazy imports for calls, contacts, and reports pages are commented out in `frontend/src/App.tsx`.
- Navigation references to archived pages are removed from `frontend/src/components/AnimatedTitle3D.tsx` and `frontend/src/components/NavBar.tsx`.
- `frontend/src/components/AuthProvider.tsx` no longer includes archived routes in its engaged route list.

To restore:

- Move files back to their original paths listed above.
- Re-enable lazy imports and `<Route>` entries in `frontend/src/App.tsx`.
- Re-add navigation entries as needed.
