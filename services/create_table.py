from database import Base, engine
from models import Station, Line, LowerTerminus, UpperTerminus

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Done!")