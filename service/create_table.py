from database import Base, engine
from model import Station, Line, LineStation

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done!")