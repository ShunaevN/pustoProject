import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import relationship
from sqlalchemy import DateTime, func
from config import Config
from .base import db
from .boost import Boost
from .enums import BoostType


class Player(db.Model):
    __tablename__ = 'players'

    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    full_name = db.Column(db.String(150), nullable=True)

    created_at = db.Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    first_login_at = db.Column(DateTime(timezone=True), nullable=True)
    last_login_at = db.Column(DateTime(timezone=True), nullable=True)

    points = db.Column(db.Integer, nullable=False, default=Config.DAILY_LOGIN_POINTS)
    boosts = relationship('Boost', back_populates='player', cascade='all, delete-orphan', lazy=True)

    def register_login(self, now: datetime | None = None) -> None:
        """
        Register a user login, set first_login_at if needed and award daily points.

        Args:
            now: time of login (datetime, optional)

        Returns:
            None object.
        """
        current_time = now or datetime.now(timezone.utc)
        today = current_time.date()

        if self.first_login_at is None:
            self.first_login_at = current_time

        if self.last_login_at is None:
            self.last_login_at = current_time

        else:
            if self.last_login_at.date() != today:
                self.points = (self.points or 0) + Config.DAILY_LOGIN_POINTS
            self.last_login_at = current_time

    def add_points(self, amount: int) -> None:
        if amount <= 0:
            return
        self.points = (self.points or 0) + amount

    def add_boost(self, boost_type: BoostType, amount: int = 1, level_id: str = None, 
                  granted_by_user_id: str = None, expires_at: datetime = None) -> Boost:
        """
        Add new boost to player (manually or after level complete)
        
        Args:
            boost_type: one of type of boost (HANDS, BOOMB, SHIELD, FREEZE, MAGNET)
            amount: amount of boost (default 1)
            level_id: ID of level for which a boost was given (None for manually)
            granted_by_user_id: ID of user who grant the boost (None для системной выдачи)
            expires_at: time of expire the boost (None for inf)
            
        Returns:
            new boost object
        """
        boost = Boost(
            id=str(uuid.uuid4()),
            player_id=self.id,
            type=boost_type,
            amount=amount,
            level_id=level_id,
            granted_by_user_id=granted_by_user_id,
            expires_at=expires_at
        )
        
        self.boosts.append(boost)
        return boost

    def add_level_completion_boost(self, level_id: str, boost_type: BoostType = None, 
                                  amount: int = 1, duration_hours: int = 24) -> Boost:
        """
        Assign a boost to the player for completing a level.
        
        Args:
            level_id: ID of the completed level.
            boost_type: Boost type to grant. If None, a random type will be chosen.
            amount: Amount of the boost.
            duration_hours: Duration of the boost in hours.
            
        Returns:
            The created boost object.
        """
        if boost_type is None:
            import random
            boost_type = random.choice(list(BoostType))
        
        expires_at = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
        
        return self.add_boost(
            boost_type=boost_type,
            amount=amount,
            level_id=level_id,
            granted_by_user_id=None,
            expires_at=expires_at
        )

    def add_manual_boost(self, boost_type: BoostType, amount: int = 1, 
                        granted_by_user_id: str = None, duration_hours: int = None) -> Boost:
        """
        Add a boost to the player manually (by an admin or the system).
        
        Args:
            boost_type: Type of the boost.
            amount: Amount of the boost.
            granted_by_user_id: ID of the user who granted the boost. None if system-granted.
            duration_hours: Duration in hours. None for a permanent boost.
            
        Returns:
            The created boost object.
        """
        expires_at = None
        if duration_hours is not None:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=duration_hours)
        
        return self.add_boost(
            boost_type=boost_type,
            amount=amount,
            level_id=None,
            granted_by_user_id=granted_by_user_id,
            expires_at=expires_at
        )



