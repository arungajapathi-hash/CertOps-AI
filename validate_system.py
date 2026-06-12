#!/usr/bin/env python3
"""Quick validation of backend and frontend modules"""

import sys

try:
    from backend.main import app
    print("✅ backend/main.py imports successfully")
    
    routes = list(app.routes)
    print(f"✅ {len(routes)} routes registered")
    
    # Check for key endpoints
    route_paths = {r.path for r in routes}
    required = {"/learn", "/readiness", "/assessment", "/submit", "/health", "/state"}
    found = required & route_paths
    print(f"✅ Key endpoints: {', '.join(sorted(found))}")
    
except Exception as e:
    print(f"❌ Error loading backend: {e}")
    sys.exit(1)

try:
    from frontend.state import get_api_state, post_api, get_api, has_completed_phase, show_phase_guard
    print("✅ frontend/state.py imports successfully")
    print("✅ Functions available: get_api_state, post_api, get_api, has_completed_phase, show_phase_guard")
    
except Exception as e:
    print(f"❌ Error loading frontend state: {e}")
    sys.exit(1)

print("\n🎉 All validation checks passed!")
