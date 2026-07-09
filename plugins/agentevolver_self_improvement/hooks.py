#!/usr/bin/env python3
"""Hooks for AgentEvolver Self-Improvement plugin."""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def install():
    """Called after plugin installation."""
    plugin_dir = Path(__file__).parent
    logger.info(f"Installing AgentEvolver Self-Improvement plugin in {plugin_dir}")
    
    # Create necessary directories if they don't exist
    (plugin_dir / "data").mkdir(exist_ok=True)
    (plugin_dir / "logs").mkdir(exist_ok=True)
    
    logger.info("AgentEvolver Self-Improvement plugin installed successfully")
    return True


def pre_update():
    """Called before plugin update."""
    logger.info("Preparing AgentEvolver Self-Improvement plugin for update")
    # Backup any important data if needed
    return True


def cleanup():
    """Optional cleanup hook (not currently called by framework)."""
    pass
