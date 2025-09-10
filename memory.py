# memory.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import json

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    risk_tolerance = Column(String, default="medium")
    income = Column(Float, default=0.0)
    goals = Column(JSON, default="[]")  # list of dicts

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    category = Column(String)
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class Portfolio(Base):
    __tablename__ = "portfolios"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    holdings = Column(JSON, default="{}")  # {symbol: shares}


def init_db(db_uri="sqlite:///pf_coach.db"):
    engine = create_engine(db_uri, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()

# convenience helpers
# def get_or_create_user(session, name="default_user"):
#     user = session.query(User).filter_by(name=name).first()
#     if not user:
#         user = User(name=name, risk_tolerance="medium", income=0.0, goals=json.dumps([]))
#         session.add(user)
#         session.commit()
#     return user

def get_or_create_user(session, name="local_user"):
    user = session.query(User).filter_by(name=name).first()
    if not user:
        user = User(name=name, income=0.0, risk_tolerance="medium",goals=json.dumps([]))
        session.add(user)
        session.commit()
    return user
