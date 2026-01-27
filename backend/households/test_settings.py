"""
Minimal Django settings for testing the households spine module.
This module is intentionally minimal and reusable - no guardian scoping.
"""
from crown_api.settings import *

# Override: Disable guardian scoping for spine module tests
HOUSEHOLDS_GUARDIAN_SCOPE_ENABLED = False
