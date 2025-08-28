from .base import db
from .player import Player
from .boost import Boost
from .enums import BoostType

# описываем все модели данных
__all__ = [
    'db',
    'Player',
    'Boost',
    'BoostType'
]