from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum as PgEnum, func
from sqlalchemy.orm import relationship
from app.models.enums import BoostType
from .base import db


class Boost(db.Model):
    __tablename__ = 'boosts'

    id = db.Column(db.String, primary_key=True)
    player_id = db.Column(db.String, db.ForeignKey('players.id'), nullable=False, index=True)

    type = db.Column(PgEnum(BoostType, name='boost_type'), nullable=False, default=BoostType.HANDS)
    amount = db.Column(db.Integer, nullable=False, default=1)

    # if we have a level model, set a foreign key to model
    level_id = db.Column(db.String, nullable=True)
    
    granted_by_user_id = db.Column(db.String, nullable=True)

    granted_at = db.Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = db.Column(DateTime(timezone=True), nullable=True)

    player = relationship('Player', back_populates='boosts')

    def is_active(self, now: datetime | None = None) -> bool:
        current_time = now or datetime.now(timezone.utc)
        return self.expires_at is None or (self.expires_at > current_time)