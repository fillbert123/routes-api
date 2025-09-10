from fastapi import FastAPI, Depends
from service.database import get_db
from sqlalchemy import text

app = FastAPI()

@app.get("/getAllStationOnRoute/{route_id}")
def read_station(route_id: int, db=Depends(get_db)):
  sql = text("""
             SELECT station.name_en, line_station.code, line_station.is_active FROM route 
             INNER JOIN route_station ON route.id = route_station.route_id 
             INNER JOIN line_station ON route_station.line_station_id = line_station.id 
             INNER JOIN station ON line_station.station_id = station.id 
             WHERE route.id = :route_id 
             ORDER BY stop_sequence ASC;
             """)
  result = db.execute(sql, {"route_id": route_id})
  return [row._asdict() for row in result]