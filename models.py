import os
import logging
import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class PlayerInfo(db.Model):
    """Modelo para armazenar informações personalizadas de jogadores"""
    id = db.Column(db.Integer, primary_key=True)
    steam_id = db.Column(db.String(120), unique=True, nullable=False, index=True)
    nickname = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    group = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    def __repr__(self):
        return f"<PlayerInfo {self.steam_id}: {self.nickname}>"