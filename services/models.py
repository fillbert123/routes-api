from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)

class Station(Base):
    __tablename__ = "station"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, index=True, unique=True)
    name = Column(String, index=True, unique=True)
    is_active = Column(Boolean, default=True, index=True)
    is_interchange = Column(Boolean, default=True, index=True)
    is_terminus = Column(Boolean, default=True, index=True)
    lower_terminus = relationship("LowerTerminus", back_populates="station")
    upper_terminus = relationship("UpperTerminus", back_populates="station")

class Line(Base):
    __tablename__ = "line"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, index=True)
    name = Column(String, index=True)

class LowerTerminus(Base):
    __tablename__ = "lower_terminus"
    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("station.id"))
    station = relationship("Station", back_populates="lower_terminus")

class UpperTerminus(Base):
    __tablename__ = "upper_terminus"
    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("station.id"))
    station = relationship("Station", back_populates="upper_terminus")