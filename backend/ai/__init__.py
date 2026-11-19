"""
Backend AI Module Shim (re-exports app.ai for top-level import compatibility)
"""
import sys
from app.ai import *
from app.ai import __all__
