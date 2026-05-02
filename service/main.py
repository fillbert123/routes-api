from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from service.database import get_db
from sqlalchemy import text

app = FastAPI(
  title="Route API",
  version="0.2.7",
  description="Route API (Reykjavik)"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/getAllRoutesByLine", tags=["v1"], deprecated=True)
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

@app.get("/getRouteStation/{route_id}", tags=["v1"], deprecated=True)
def get_route_station(route_id: int, db=Depends(get_db)):
  sql = text("""
    SELECT 
      s.id station_id,
      s.name_en station_name,
      s.is_active station_is_active,
      ls2.code line_station_code,
      ls2.is_active line_station_is_active,
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
        "station_is_active": row["station_is_active"],
        "stop_sequence": row["stop_sequence"],
        "interchanges": []
      }
    grouped[key]["interchanges"].append({
      "line_color": row["line_color"],
      "line_station_code": row["line_station_code"],
      "line_station_is_active": row["line_station_is_active"],
      "route_group_code": row["route_group_code"]
    })
  data = list(grouped.values())
  return data

@app.get("/getRouteDetail/{station_id}", tags=["v1"], deprecated=True)
def get_route_detail(station_id: int, db=Depends(get_db)):
  SPECIAL_LRT_STATION = {104, 193, 194, 195, 196}
  if station_id in SPECIAL_LRT_STATION:
    sql = text("""
      SELECT DISTINCT ON (s2.id)
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
      ORDER BY s2.id, rs.stop_sequence DESC;
    """)
  else:
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

@app.get("/getRouteByRouteGroupId/{route_group_id}", tags=["v1"], deprecated=True)
def get_route_by_route_group_id(route_group_id: int, db=Depends(get_db)):
  sql = text("""
    SELECT
      r.id route_id,
      r.route_group_id route_group_id,
      s1.name_en start_station_name,
      s2.name_en end_station_name,
	    s3.name_en complete_start_station_name,
	    s4.name_en complete_end_station_name
    FROM route r
    JOIN line_station ls1 ON ls1.id = r.start_station_id
    JOIN line_station ls2 ON ls2.id = r.end_station_id
	  JOIN line_station ls3 ON ls3.id = r.complete_start_station_id
	  JOIN line_station ls4 ON ls4.id = r.complete_end_station_id
    JOIN station s1 ON s1.id = ls1.station_id
    JOIN station s2 ON s2.id = ls2.station_id
	  JOIN station s3 ON s3.id = ls3.station_id
	  JOIN station s4 ON s4.id = ls4.station_id
    WHERE r.route_group_id = :route_group_id
    ORDER BY r.id;
  """)
  result = [row._asdict() for row in db.execute(sql, {"route_group_id": route_group_id})]
  data = result
  return data

@app.get("/getSearchStationResult/{query}", tags=["v1"], deprecated=False)
def get_search_station_result(query: str, db=Depends(get_db)):
  sql = text("""             
    SELECT 
	    s.id station_id,
      s.name_en station_name,
      ls.code line_code,
      l.color line_color
    FROM station s
    JOIN line_station ls ON ls.station_id = s.id
    JOIN line l ON l.id = ls.line_id
    WHERE LOWER(s.name_en) LIKE LOWER(:query)
    ORDER BY l.id;
  """)
  result = [row._asdict() for row in db.execute(sql, {"query": '%' + query + '%'})]
  grouped = {}
  for row in result:
    key = (row["station_id"], row["station_name"])
    if key not in grouped:
      grouped[key] = {
        "station_id": row["station_id"],
        "station_name": row["station_name"],
        "interchanges": []
      }
    grouped[key]["interchanges"].append({
      "line_station_code": row["line_code"],
      "line_color": row["line_color"]
    })
  data = list(grouped.values())
  return data

@app.get("/getAllLine", tags=["v2"], deprecated=False)
def get_all_line(db=Depends(get_db)):
  sql = text("""
    SELECT 
      l.id AS line_id,
      l.name AS line_name,
      l.code AS line_code,
      l.color AS line_color,
      l.is_active AS line_is_active,
      rg.id AS route_group_id,
      rg.name AS route_group_name,
      rg.code AS route_group_code,
      s.name_en AS route_group_terminus,
      s2.name_en AS route_group_via
    FROM LINE l
    LEFT JOIN ROUTE_GROUP rg ON rg.line_id = l.id
    LEFT JOIN ROUTE r ON r.route_group_id = rg.id
    LEFT JOIN LINE_STATION ls ON ls.id = r.start_station_id
    LEFT JOIN STATION s ON s.id = ls.station_id
    LEFT JOIN LINE_STATION ls2 ON ls2.id = r.via_station_id
    LEFT JOIN STATION s2 ON s2.id = ls2.station_id
    ORDER BY r.id ASC;
  """)

  result = [row._asdict() for row in db.execute(sql)]
  grouped = {}
  for row in result:
    line_key = row["line_id"]
    if line_key not in grouped:
      grouped[line_key] = {
        "id": row["line_id"],
        "name": row["line_name"],
        "code": row["line_code"],
        "color": row["line_color"],
        "isActive": row["line_is_active"],
        "routeGroup": {}
      }
    route_group_key = row["route_group_id"]
    if route_group_key not in grouped[line_key]["routeGroup"]:
      grouped[line_key]["routeGroup"][route_group_key] = {
        "id": row["route_group_id"],
        "name": row["route_group_name"],
        "code": row["route_group_code"],
        "terminus": []
      }
    grouped[line_key]["routeGroup"][route_group_key]["terminus"].append(row["route_group_terminus"])
    if row["route_group_via"] is not None:
      if "via" not in grouped[line_key]["routeGroup"][route_group_key]:
        grouped[line_key]["routeGroup"][route_group_key]["via"] = []
      grouped[line_key]["routeGroup"][route_group_key]["via"].append(row["route_group_via"])
  for line in grouped.values():
    line["routeGroup"] = list(line["routeGroup"].values())
  return list(grouped.values())

@app.get("/getRouteGroup/{routeGroupId}", tags=["v2"], deprecated=False)
def get_route_group(routeGroupId: int, db=Depends(get_db)):
  sql = text("""
    SELECT
      rg.id AS route_group_id,
      rg.name AS route_group_name,
      rg.code AS route_group_code,
      l.color AS route_group_color,
      r.is_active AS route_group_is_active,
      r.id AS route_id,
      s.name_en AS route_current_terminus_start_name,
      s2.name_en AS route_current_terminus_end_name,
      s3.name_en AS route_complete_terminus_start_name,
      s4.name_en AS route_complete_terminus_end_name
    FROM ROUTE r
    LEFT JOIN ROUTE_GROUP rg ON rg.id = r.route_group_id
    LEFT JOIN LINE l ON l.id = rg.line_id
    LEFT JOIN LINE_STATION ls ON ls.id = r.start_station_id
    LEFT JOIN STATION s ON s.id = ls.station_id
    LEFT JOIN LINE_STATION ls2 ON ls2.id = r.end_station_id
    LEFT JOIN STATION s2 ON s2.id = ls2.station_id
    LEFT JOIN LINE_STATION ls3 ON ls3.id = r.complete_start_station_id
    LEFT JOIN STATION s3 ON s3.id = ls3.station_id
    LEFT JOIN LINE_STATION ls4 ON ls4.id = r.complete_end_station_id
    LEFT JOIN STATION s4 ON s4.id = ls4.station_id
    WHERE rg.id = :routeGroupId
    ORDER BY r.id ASC;
  """)

  result = [row._asdict() for row in db.execute(sql, {"routeGroupId": routeGroupId})]
  grouped = {}
  for row in result:
    route_group_key = row["route_group_id"]
    if route_group_key not in grouped:
      grouped[route_group_key] = {
        "id": row["route_group_id"],
        "name": row["route_group_name"],
        "code": row["route_group_code"],
        "color": row["route_group_color"],
        "isActive": row["route_group_is_active"],
        "route": []
      }
    grouped[route_group_key]["route"].append({
      "id": row["route_id"],
      "currentTerminus": {
        "startName": row["route_current_terminus_start_name"],
        "endName": row["route_current_terminus_end_name"]
      },
      "completeTerminus": {
        "startName": row["route_complete_terminus_start_name"],
        "endName": row["route_complete_terminus_end_name"]
      }
    })
  for group in grouped.values():
    if group["route"]:
      group["route"].append(group["route"].pop(0))

  return next(iter(grouped.values()))

@app.get("/getRoute/{routeId}", tags=["v2"], deprecated=False)
def get_route(routeId: int, db=Depends(get_db)):
  sql = text("""
    SELECT 
	    r.id AS route_id,
	    r.is_active AS route_is_active,
      rs.stop_sequence AS station_stop_sequence,
      s.id AS station_id,
      s.name_en AS station_name,
      ls.code AS station_code,
      ls.is_active AS station_is_active,
      ls2.id AS station_interchange_id,
      rg.code AS station_interchange_code,
      ls2.code AS station_interchange_station_code,
      l.color AS station_interchange_color,
      ls2.is_active AS station_interchange_is_active
    FROM route r
    JOIN route_station rs ON rs.route_id = r.id
    JOIN line_station ls ON ls.id = rs.line_station_id
    JOIN station s ON s.id = ls.station_id
    JOIN line_station ls2 ON ls2.station_id = s.id
    JOIN line l ON l.id = ls2.line_id
    JOIN route_group rg ON rg.id = ls2.route_group_id
    WHERE r.id = :routeId
    ORDER BY rs.stop_sequence, rg.id;
  """)
  result = [row._asdict() for row in db.execute(sql, {"routeId": routeId})]
  grouped = {}
  for row in result:
    route_key = row["route_id"]
    if route_key not in grouped:
      grouped[route_key] = {
        "id": row["route_id"],
        "isActive": row["route_is_active"],
        "station": {}
      }
    station_key = row["station_stop_sequence"]
    if station_key not in grouped[route_key]["station"]:
      grouped[route_key]["station"][station_key] = {
        "id": row["station_id"],
        "name": row["station_name"],
        "code": row["station_code"],
        "isActive": row["station_is_active"],
        "interchange": []
      }
    if row["station_code"] != row["station_interchange_station_code"]:
      grouped[route_key]["station"][station_key]["interchange"].append({
        "id": row["station_interchange_id"],
        "code": row["station_interchange_code"],
        "color": row["station_interchange_color"],
        "isActive": row["station_interchange_is_active"]
      })

  for route in grouped.values():
    route["station"] = list(route.get("station", {}).values())
  
  return next(iter(grouped.values()))

@app.get("/getStation/{stationId}", tags=["v2"], deprecated=False)
def get_station(stationId: int, db=Depends(get_db)):
  sqlGetStation = ""
  SPECIAL_LRT_STATION_ID = {104, 193, 194, 195, 196}
  SPECIAL_LRT_ROUTE_GROUP_ID = 13
  if(stationId in SPECIAL_LRT_STATION_ID):
    sqlGetStation = text("""
      SELECT DISTINCT ON (s2.id)
        s.id AS station_id,
        s.name_en AS station_name,
        s.is_active AS station_is_active,
        l.id AS line_id,
        l.name AS line_name,
        l.code AS line_code,
        l.color AS line_color,
        l.is_active AS line_is_active,
        rg.id AS route_group_id,
        rg.name AS route_group_name,
        rg.code AS route_group_code,
        ls.is_active AS route_is_active,
        rs.route_id AS route_id,
        s.id AS current_station_id,
        s.name_en AS current_station_name,
        ls.code AS current_station_code,
        s2.id AS next_station_id,
        s2.name_en AS next_station_name,
        ls2.code AS next_station_code,
        s3.id AS end_station_id,
        s3.name_en AS end_station_name,
        ls3.code AS end_station_code
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
      WHERE s.id = :stationId
      ORDER BY s2.id, rs.stop_sequence DESC;
    """)
  else:
    sqlGetStation = text("""
      SELECT DISTINCT ON (rs.route_id)
        s.id AS station_id,
        s.name_en AS station_name,
        s.is_active AS station_is_active,
        l.id AS line_id,
        l.name AS line_name,
        l.code AS line_code,
        l.color AS line_color,
        l.is_active AS line_is_active,
        rg.id AS route_group_id,
        rg.name AS route_group_name,
        rg.code AS route_group_code,
        ls.is_active AS route_is_active,
        rs.route_id AS route_id,
        s.id AS current_station_id,
        s.name_en AS current_station_name,
        ls.code AS current_station_code,
        s2.id AS next_station_id,
        s2.name_en AS next_station_name,
        ls2.code AS next_station_code,
        s3.id AS end_station_id,
        s3.name_en AS end_station_name,
        ls3.code AS end_station_code
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
      where s.id = :stationId
      ORDER BY rs.route_id, rs.stop_sequence DESC;
    """)

  resultGetStation = [row._asdict() for row in db.execute(sqlGetStation, {"stationId": stationId})]
  grouped = {}
  for row in resultGetStation:
    station_key = row["station_id"]
    if station_key not in grouped:
      grouped[station_key] = {
        "id": row["station_id"],
        "name": row["station_name"],
        "isActive": row["station_is_active"],
        "line": {}
      }
    line_key = row["line_id"]
    if line_key not in grouped[station_key]["line"]:
      grouped[station_key]["line"][line_key] = {
        "id": row["line_id"],
        "name": row["line_name"],
        "code": row["line_code"],
        "color": row["line_color"],
        "isActive": row["line_is_active"],
        "routeGroup": {}
      }
    route_group_key = row["route_group_id"]
    if(route_group_key) not in grouped[station_key]["line"][line_key]["routeGroup"]:
      grouped[station_key]["line"][line_key]["routeGroup"][route_group_key] = {
        "id": row["route_group_id"],
        "name": row["route_group_name"],
        "code": row["route_group_code"],
        "isActive": row["route_is_active"],
        "currentStation": {
          "id": row["current_station_id"],
          "name": row["current_station_name"],
          "code": row["current_station_code"]
        },
      }
    
    LOOP_LINE_ID = {10, 11}
    if(line_key in LOOP_LINE_ID):
      if("nextStation" not in grouped[station_key]["line"][line_key]["routeGroup"][route_group_key]):
        grouped[station_key]["line"][line_key]["routeGroup"][route_group_key]["nextStation"] = {
          "id": row["next_station_id"],
          "name": row["next_station_name"],
          "code": row["next_station_code"],
          "terminus": {
            "id": [row["end_station_id"]],
            "name": [row["end_station_name"]]
          }
        }
      elif("previousStation" not in grouped[station_key]["line"][line_key]["routeGroup"][route_group_key]):
        grouped[station_key]["line"][line_key]["routeGroup"][route_group_key]["previousStation"] = {
          "id": row["next_station_id"],
          "name": row["next_station_name"],
          "code": row["next_station_code"],
          "terminus": {
            "id": [row["end_station_id"]],
            "name": [row["end_station_name"]]
          }
        }
    elif(route_group_key != SPECIAL_LRT_ROUTE_GROUP_ID):
      sqlGetRouteGroupTerminus = text("""
        SELECT
          s.id AS terminus_id,
          s.name_en AS terminus_name,
          s2.id AS complete_terminus_id,
          s2.name_en AS complete_terminus_name
        FROM ROUTE_GROUP rg
        JOIN ROUTE r ON r.route_group_id = rg.id
        JOIN LINE_STATION ls ON ls.id = r.start_station_id
        JOIN STATION s ON s.id = ls.station_id
        JOIN LINE_STATION ls2 ON ls2.id = r.complete_start_station_id
        JOIN STATION s2 ON s2.id = ls2.station_id
        WHERE rg.id = :routeGroupId
        ORDER BY r.id ASC;
      """)

      resultRouteGroupTerminus = [row._asdict() for row in db.execute(sqlGetRouteGroupTerminus, {"routeGroupId": row["route_group_id"]})]
      startTerminus = resultRouteGroupTerminus[0]
      if(row["end_station_id"] == startTerminus['terminus_id']):
        grouped[station_key]["line"][line_key]["routeGroup"][route_group_key]["previousStation"] = {
          "id": row["next_station_id"],
          "name": row["next_station_name"],
          "code": row["next_station_code"],
          "terminus": {
            "id": [startTerminus['terminus_id']],
            "name": [startTerminus['terminus_name']]
          }
        }

      endTerminus = resultRouteGroupTerminus[1]
      if(row["end_station_id"] == endTerminus['terminus_id']):
        grouped[station_key]["line"][line_key]["routeGroup"][route_group_key]["nextStation"] = {
          "id": row["next_station_id"],
          "name": row["next_station_name"],
          "code": row["next_station_code"],
          "terminus": {
            "id": [endTerminus['terminus_id']],
            "name": [endTerminus['terminus_name']]
          }
        }
        
      branchTerminus = {}
      if(len(resultRouteGroupTerminus) == 3):
        branchTerminus = resultRouteGroupTerminus[2]
        if(row["end_station_id"] == branchTerminus['terminus_id']):
          grouped[station_key]["line"][line_key]["routeGroup"][route_group_key]["branchStation"] = {
            "id": row["next_station_id"],
            "name": row["next_station_name"],
            "code": row["next_station_code"],
            "terminus": {
              "id": [branchTerminus['terminus_id']],
              "name": [branchTerminus['terminus_name']]
            }
          }
      
      route_group = grouped[station_key]["line"][line_key]["routeGroup"][route_group_key]
      if("nextStation" in route_group and "branchStation" in route_group):
        grouped[station_key]["line"][line_key]["routeGroup"][route_group_key]["previousStation"] = grouped[station_key]["line"][line_key]["routeGroup"][route_group_key]["nextStation"]
        grouped[station_key]["line"][line_key]["routeGroup"][route_group_key]["nextStation"] = grouped[station_key]["line"][line_key]["routeGroup"][route_group_key]["branchStation"]
    else:
      if("previousStation" not in grouped[station_key]["line"][line_key]["routeGroup"][route_group_key]):
        grouped[station_key]["line"][line_key]["routeGroup"][route_group_key]["previousStation"] = {
          "id": row["next_station_id"],
          "name": row["next_station_name"],
          "code": row["next_station_code"],
          "terminus": {
            "id": [row["end_station_id"]],
            "name": [row["end_station_name"]]
          }
        }
      elif("nextStation" not in grouped[station_key]["line"][line_key]["routeGroup"][route_group_key]):
        grouped[station_key]["line"][line_key]["routeGroup"][route_group_key]["nextStation"] = {
          "id": row["next_station_id"],
          "name": row["next_station_name"],
          "code": row["next_station_code"],
          "terminus": {
            "id": [row["end_station_id"]],
            "name": [row["end_station_name"]]
          }
        }
      elif("branchStation" not in grouped[station_key]["line"][line_key]["routeGroup"][route_group_key]):
        grouped[station_key]["line"][line_key]["routeGroup"][route_group_key]["branchStation"] = {
          "id": row["next_station_id"],
          "name": row["next_station_name"],
          "code": row["next_station_code"],
          "terminus": {
            "id": [row["end_station_id"]],
            "name": [row["end_station_name"]]
          }
        }

    root_route_group = grouped[station_key]["line"][line_key]["routeGroup"]
    if("branchStation" in root_route_group[route_group_key]):
      if("nextStation" in root_route_group[route_group_key]):
        if(root_route_group[route_group_key]["nextStation"]["id"] == root_route_group[route_group_key]["branchStation"]["id"]):
          root_route_group[route_group_key]["nextStation"]["terminus"]["id"].append(root_route_group[route_group_key]["branchStation"]["terminus"]["id"][0])
          root_route_group[route_group_key]["nextStation"]["terminus"]["name"].append(root_route_group[route_group_key]["branchStation"]["terminus"]["name"][0])
          root_route_group[route_group_key].pop("branchStation", None)
      elif("previousStation" in root_route_group[route_group_key]):
        if(root_route_group[route_group_key]["previousStation"]["id"] == root_route_group[route_group_key]["branchStation"]["id"]):
          root_route_group[route_group_key]["previousStation"]["terminus"]["id"].append(root_route_group[route_group_key]["branchStation"]["terminus"]["id"][0])
          root_route_group[route_group_key]["previousStation"]["terminus"]["name"].append(root_route_group[route_group_key]["branchStation"]["terminus"]["name"][0])
          root_route_group[route_group_key].pop("branchStation", None)
    if("nextStation" in root_route_group[route_group_key] and "previousStation" in root_route_group[route_group_key]):
      if(root_route_group[route_group_key]["nextStation"]["id"] == root_route_group[route_group_key]["previousStation"]["id"]):
        if(root_route_group[route_group_key]["nextStation"]["terminus"]["id"] != root_route_group[route_group_key]["previousStation"]["terminus"]["id"]):
          root_route_group[route_group_key]["nextStation"]["terminus"]["id"].append(root_route_group[route_group_key]["previousStation"]["terminus"]["id"][0])
          root_route_group[route_group_key]["nextStation"]["terminus"]["name"].append(root_route_group[route_group_key]["previousStation"]["terminus"]["name"][0])
        root_route_group[route_group_key].pop("previousStation", None)

  for station in grouped.values():
    station["line"] = [
      {
        **line,
        "routeGroup": list(line.get("routeGroup", {}).values())
      }
      for line in station.get("line", {}).values()
    ]
  return next(iter(grouped.values()))