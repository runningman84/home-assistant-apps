"""Compatibility shim for modules that import `base` at top-level.

Some app modules import `from base import BaseApp`. In the test
environment `apps.base` is the real implementation; expose a small
shim so those imports resolve.
"""
from apps.base import BaseApp

__all__ = ["BaseApp"]
