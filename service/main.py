from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from service.database import get_db
from sqlalchemy import text

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/getAllRoutesByLine")
def get_all_routes_by_line(db=Depends(get_db)):
  sql = text("""
    SELECT 
      l.code line_code, 
      l.name line_name, 
      l.color line_color, 
      l.is_active line_is_active, 
      rg.id route_group_id, 
      rg.name route_group_name, 
      rg.code route_group_code, 
      r.is_active route_is_active, 
      s1.name_en route_start_station_name, 
      s2.name_en route_end_station_name, 
      s3.name_en route_via_station_name
    FROM line l
    LEFT JOIN route_group rg ON l.id = rg.line_id
    LEFT JOIN route r ON rg.id = r.route_group_id
    LEFT JOIN line_station ls1 ON ls1.id = r.start_station_id
    LEFT JOIN station s1 ON s1.id = ls1.station_id
    LEFT JOIN line_station ls2 ON ls2.id = r.end_station_id
    LEFT JOIN station s2 ON s2.id = ls2.station_id
    LEFT JOIN line_station ls3 ON ls3.id = r.via_station_id
    LEFT JOIN station s3 ON s3.id = ls3.station_id
    ORDER BY r.id;
  """)

  result = [row._asdict() for row in db.execute(sql)]
  grouped = {}

  for row in result:
    line_key = (row["line_code"], row["line_name"], row["line_color"], row["line_is_active"])
    if line_key not in grouped:
      grouped[line_key] = {
        "line_code": row["line_code"],
        "line_name": row["line_name"],
        "line_color": row["line_color"],
        "line_is_active": row["line_is_active"],
        "route_groups": {}
      }
    line = grouped[line_key]
    group_key = (row["route_group_id"])
    if group_key not in line["route_groups"]:
      line["route_groups"][group_key] = {
        "route_group_id": row["route_group_id"],
        "route_group_name": row["route_group_name"],
        "route_group_code": row["route_group_code"],
        "route_is_active": row["route_is_active"],
        "routes": []
      }
    route_group = line["route_groups"][group_key]
    route_group["routes"].append({
      "route_start_station_name": row["route_start_station_name"],
      "route_end_station_name": row["route_end_station_name"],
      "route_via_station_name": row["route_via_station_name"]
    })
  data = []
  for line in grouped.values():
    line["route_groups"] = list(line["route_groups"].values())
    data.append(line)
  return data

@app.get("/getRouteStation/{route_id}")
def get_route_station(route_id: int, db=Depends(get_db)):
  sql = text("""
    SELECT 
        s.id station_id,
        s.name_en station_name,
        ls2.code line_station_code,
        rs.stop_sequence stop_sequence,
      l.color line_color,
      rg.code route_group_code
    FROM route r
    JOIN route_station rs ON rs.route_id = r.id
    JOIN line_station ls ON ls.id = rs.line_station_id
    JOIN station s ON s.id = ls.station_id
    JOIN line_station ls2 ON ls2.station_id = s.id
    JOIN line l ON l.id = ls2.line_id
    JOIN route_group rg ON rg.id = ls2.route_group_id
    WHERE r.id = :route_id 
    ORDER BY rs.stop_sequence, rg.id;
  """)
  result = [row._asdict() for row in db.execute(sql, {"route_id": route_id})]
  grouped = {}
  for row in result:
    key = (row["station_id"], row["station_name"], row["stop_sequence"])
    if key not in grouped:
      grouped[key] = {
        "station_id": row["station_id"],
        "station_name": row["station_name"],
        "stop_sequence": row["stop_sequence"],
        "interchanges": []
      }
    grouped[key]["interchanges"].append({
      "line_color": row["line_color"],
      "line_station_code": row["line_station_code"],
      "route_group_code": row["route_group_code"]
    })
  data = list(grouped.values())
  return data

@app.get("/getRouteDetail/{station_id}")
def get_route_detail(station_id: int, db=Depends(get_db)):
  sql = text("""
    SELECT DISTINCT ON (rs.route_id)
      s.name_en current_station_name,
      ls.code current_station_code,
      l.code line_code,
      l.name line_name,
      l.color line_color,
      rg.id route_group_id,
      rg.code route_group_code,
      rs.route_id route_id,
      s2.id next_station_id,
      s2.name_en next_station_name,
      ls2.code next_station_code,
      s3.id end_station_id,
      s3.name_en end_station_name,
      ls3.code end_station_code
    FROM station s 
    JOIN line_station ls ON ls.station_id = s.id
    JOIN line l ON l.id = ls.line_id
    JOIN route_group rg ON rg.id = ls.route_group_id
    JOIN route_station rs ON rs.line_station_id = ls.id
    JOIN route_station rs2 ON rs2.stop_sequence = rs.stop_sequence + 1 AND rs2.route_id = rs.route_id
    JOIN line_station ls2 ON ls2.id = rs2.line_station_id
    JOIN station s2 ON s2.id = ls2.station_id
    JOIN route r ON r.id = rs2.route_id
    JOIN line_station ls3 ON ls3.id = r.end_station_id
    JOIN station s3 ON s3.id = ls3.station_id
    WHERE s.id = :station_id
    ORDER BY rs.route_id, rs.stop_sequence DESC;
  """)
  result = [row._asdict() for row in db.execute(sql, {"station_id": station_id})]
  grouped = {}
  for row in result:
    line_key = row["line_code"]
    if line_key not in grouped:
      grouped[line_key] = {
        "line_code": row["line_code"],
        "line_name": row["line_name"],
        "line_color": row["line_color"],
        "track": []
      }
    track_key = (
      row["current_station_name"],
      row["current_station_code"],
      row["route_group_code"]
    )
    track = next((
        t for t in grouped[line_key]["track"]
        if (
          t["current_station_name"],
          t["current_station_code"],
          t["route_group"]
        ) == track_key
      ),
      None
    )
    if track is None:
      track = {
        "current_station_name": row["current_station_name"],
        "current_station_code": row["current_station_code"],
        "route_group_id": row["route_group_id"],
        "route_group": row["route_group_code"],
        "next_station": []
      }
      grouped[line_key]["track"].append(track)
    track["next_station"].append({
      "next_station_id": row["next_station_id"],
      "next_station_name": row["next_station_name"],
      "next_station_code": row["next_station_code"],
      "end_station_id": row["end_station_id"],
      "end_station_name": row["end_station_name"],
      "end_station_code": row["end_station_code"]
    })
  data = list(grouped.values())
  return data

@app.get("/getRouteByRouteGroupId/{route_group_id}")
def get_route_by_route_group_id(route_group_id: int, db=Depends(get_db)):
  sql = text("""
    SELECT
      r.id,
      r.route_group_id,
      s1.name_en,
      s2.name_en
    FROM route r
    JOIN line_station ls1 ON ls1.id = r.start_station_id
    JOIN line_station ls2 ON ls2.id = r.end_station_id
    JOIN station s1 ON s1.id = ls1.station_id
    JOIN station s2 ON s2.id = ls2.station_id
    WHERE r.route_group_id = :route_group_id
    ORDER BY r.id;
  """)
  result = [row._asdict() for row in db.execute(sql, {"route_group_id": route_group_id})]
  data = result
  return data