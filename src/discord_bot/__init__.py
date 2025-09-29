"""
Module du bot Discord
"""

from .bot import AlternanceBot
from .webhook import WebhookNotifier

__all__ = [
    'AlternanceBot',
    'WebhookNotifier'
]