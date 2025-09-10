from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship
from service.database import Base

class Station(Base):
  __tablename__ = "station"
  id = Column(Integer, primary_key=True, index=True)
  name_en = Column(String, index=True)
  name_ms = Column(String, index=True)
  name_zh = Column(String, index=True)
  name_ta = Column(String, index=True)
  is_active = Column(Boolean, index=True)
  line_station = relationship("LineStation", back_populates="station")

class Line(Base):
  __tablename__ = "line"
  id = Column(Integer, primary_key=True, index=True)
  code = Column(String, index=True)
  name = Column(String, index=True)
  type = Column(String, index=True)
  color = Column(String, index=True)
  is_active = Column(Boolean, index=True)
  line_station = relationship("LineStation", back_populates="line")
  route_groups = relationship("RouteGroup", back_populates="line")

class LineStation(Base):
  __tablename__ = "line_station"
  id = Column(Integer, primary_key=True, index=True)
  code = Column(String, index=True)
  station = relationship("Station", back_populates="line_station")
  station_id = Column(Integer, ForeignKey("station.id"))
  line = relationship("Line", back_populates="line_station")
  line_id = Column(Integer, ForeignKey("line.id"))
  is_active = Column(Boolean, index=True)
  # route = relationship("Route", back_populates="line_station")
  route_station = relationship("RouteStation", back_populates="line_station")

class RouteGroup(Base):
  __tablename__ = "route_group"
  id = Column(Integer, primary_key=True, index=True)
  line = relationship("Line", back_populates="route_groups")
  line_id = Column(Integer, ForeignKey("line.id"))
  name = Column(String, index=True)
  route = relationship("Route", back_populates="route_group")

class Route(Base):
  __tablename__ = "route"
  id = Column(Integer, primary_key=True, index=True)
  route_group = relationship("RouteGroup", back_populates="route")
  route_group_id = Column(Integer, ForeignKey("route_group.id"))
  # line_station = relationship("LineStation", back_populates="route")
  start_station_id = Column(Integer, ForeignKey("line_station.id"))
  end_station_id = Column(Integer, ForeignKey("line_station.id"))
  via_station_id = Column(Integer, ForeignKey("line_station.id"))
  start_station = relationship("LineStation", foreign_keys=[start_station_id])
  end_station = relationship("LineStation", foreign_keys=[end_station_id])
  via_station = relationship("LineStation", foreign_keys=[via_station_id])
  name = Column(String, index=True)
  is_branch = Column(Boolean, index=True)
  is_loop = Column(Boolean, index=True)
  is_active = Column(Boolean, index=True)
  route_station = relationship("RouteStation", back_populates="route")

class RouteStation(Base):
  __tablename__ = "route_station"
  id = Column(Integer, primary_key=True, index=True)
  route = relationship("Route", back_populates="route_station")
  route_id = Column(Integer, ForeignKey("route.id"))
  line_station = relationship("LineStation", back_populates="route_station")
  line_station_id = Column(Integer, ForeignKey("line_station.id"))
  stop_sequence = Column(Integer, index=True)