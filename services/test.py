from fastapi import FastAPI, Path, HTTPException, status
from typing import Optional
from pydantic import BaseModel

app = FastAPI()
class Item(BaseModel):
  name: str
  price: float
  brand: Optional[str] = None

class UpdateItem(BaseModel):
  name: Optional[str] = None
  price: Optional[float] = None
  brand: Optional[str] = None

# @app.get("/")
# def home():
#   return {"Data": "Testing"}

# @app.get("/about")
# def about():
#   return {"Data": "About"}

inventory = {}

@app.get("/get-item/{item_id}")
def get_item(item_id: int = Path(description = "The ID of the item you'd like to view")):
  return inventory[item_id]

@app.get("/get-item-name/{item_id}")
def get_item(*, item_id: int, name: str = None, test: int):
  for item_id in inventory:
    if inventory[item_id].name == name:
      return inventory[item_id]
  raise HTTPException(status_code = 404, detail = "Item name not found.")
@app.post("/create-item/{item_id}")
def create_item(item_id: int, item: Item):
  if item_id in inventory:
    raise HTTPException(status_code = 400, detail = "Item ID already exist.")
  inventory[item_id] = item
  return inventory[item_id]

@app.put("/update-item/{item_id}")
def update_item(item_id: int, item: UpdateItem):
  if item_id not in inventory:
    raise HTTPException(status_code = 404, detail = "Item ID does not exist.")
  if item.name != None:
    inventory[item_id].name = item.name
  if item.price != None:
    inventory[item_id].price = item.price
  if item.brand != None:
    inventory[item_id].brand = item.brand
  return inventory[item_id]