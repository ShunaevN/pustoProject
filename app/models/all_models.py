import csv
from datetime import date, datetime
from sqlalchemy.orm import relationship
from .base import db


class Player(db.Model):
    __tablename__ = 'dj_players'

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.String(100), nullable=False, index=True)
    levels = relationship('PlayerLevel', back_populates='player', cascade='all, delete-orphan', lazy=True)


class Level(db.Model):
    __tablename__ = 'dj_levels'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    order = db.Column(db.Integer, nullable=False, default=0)

    player_levels = relationship('PlayerLevel', back_populates='level', cascade='all, delete-orphan', lazy=True)
    prizes = relationship('LevelPrize', back_populates='level', cascade='all, delete-orphan', lazy=True)


class Prize(db.Model):
    __tablename__ = 'dj_prizes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)

    level_prizes = relationship('LevelPrize', back_populates='prize', cascade='all, delete-orphan', lazy=True)


class PlayerLevel(db.Model):
    __tablename__ = 'dj_player_levels'

    id = db.Column(db.Integer, primary_key=True)

    player_id = db.Column(db.Integer, db.ForeignKey('dj_players.id', ondelete='CASCADE'), nullable=False, index=True)
    level_id = db.Column(db.Integer, db.ForeignKey('dj_levels.id', ondelete='CASCADE'), nullable=False, index=True)

    completed = db.Column(db.Date, nullable=True)
    is_completed = db.Column(db.Boolean, nullable=False, default=False)
    score = db.Column(db.Integer, nullable=False, default=0)

    player = relationship('Player', back_populates='levels')
    level = relationship('Level', back_populates='player_levels')


class LevelPrize(db.Model):
    __tablename__ = 'dj_level_prizes'

    id = db.Column(db.Integer, primary_key=True)

    level_id = db.Column(db.Integer, db.ForeignKey('dj_levels.id', ondelete='CASCADE'), nullable=False, index=True)
    prize_id = db.Column(db.Integer, db.ForeignKey('dj_prizes.id', ondelete='CASCADE'), nullable=False, index=True)

    received = db.Column(db.Date, nullable=True)

    level = relationship('Level', back_populates='prizes')
    prize = relationship('Prize', back_populates='level_prizes')


# -----------------------------
# Service functions
# -----------------------------

def assign_prize_to_player_level(player_public_id: str, level_id: int, prize_id: int, 
                                 received_on: datetime = None, session=None) -> LevelPrize:
    """
    Assign a prize to a player's level completion.

    Args:
        player_public_id: Public player identifier stored in Player.player_id.
        level_id: Level primary key (dj_levels.id).
        prize_id: Prize primary key (dj_prizes.id).
        received_on: Date when the prize is received (defaults to today).
        session: Optional SQLAlchemy session (defaults to db.session).

    Returns:
        Created or updated LevelPrize row.

    Notes:
        - Ensures PlayerLevel exists; marks it completed and sets completion date if needed.
        - Creates LevelPrize for the level if not existing; updates received date otherwise.
          This schema links prizes to levels, not to a specific player.
    """
    session = session or db.session
    received_on = received_on or date.today()

    player = session.query(Player).filter(Player.player_id == player_public_id).first()
    if player is None:
        raise ValueError("Player not found by player_id")

    level = session.get(Level, level_id)
    if level is None:
        raise ValueError("Level not found")

    prize = session.get(Prize, prize_id)
    if prize is None:
        raise ValueError("Prize not found")

    pl = (
        session.query(PlayerLevel)
        .filter(PlayerLevel.player_id == player.id, PlayerLevel.level_id == level.id)
        .first()
    )
    if pl is None:
        pl = PlayerLevel(player_id=player.id, level_id=level.id, is_completed=True, completed=received_on)
        session.add(pl)
    else:
        if not pl.is_completed:
            pl.is_completed = True
        if pl.completed is None:
            pl.completed = received_on

    lp = (
        session.query(LevelPrize)
        .filter(LevelPrize.level_id == level.id, LevelPrize.prize_id == prize.id)
        .first()
    )
    if lp is None:
        lp = LevelPrize(level_id=level.id, prize_id=prize.id, received=received_on)
        session.add(lp)
    else:
        lp.received = received_on

    session.commit()
    return lp


def export_player_levels_to_csv(file_path: str, session=None, chunk_size: int = 5000) -> None:
    """
    Stream-export player-level data to CSV: player_id, level title, completion flag, level prize title.

    Designed for 100k+ rows using chunked iteration (yield_per) to keep memory usage low.

    Args:
        file_path: Path to write the CSV file (UTF-8, comma-separated).
        session: Optional SQLAlchemy session (defaults to db.session).
        chunk_size: Rows fetched per batch.
    """
    session = session or db.session

    q = (
        session.query(
            Player.player_id.label('player_public_id'),
            Level.title.label('level_title'),
            PlayerLevel.is_completed.label('is_completed'),
            Prize.title.label('prize_title'),
        )
        .join(PlayerLevel, Player.id == PlayerLevel.player_id)
        .join(Level, Level.id == PlayerLevel.level_id)
        .outerjoin(LevelPrize, LevelPrize.level_id == Level.id)
        .outerjoin(Prize, Prize.id == LevelPrize.prize_id)
        .order_by(Player.id, Level.id)
    )

    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['player_id', 'level_title', 'is_completed', 'prize_title'])

        for row in q.yield_per(chunk_size):
            writer.writerow([
                row.player_public_id,
                row.level_title,
                '1' if row.is_completed else '0',
                row.prize_title or '',
            ])