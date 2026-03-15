import sqlite3
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

api_app = FastAPI()

def init_db():
    conn = sqlite3.connect("online_repair.db")
    cursor = conn.cursor()
    # Table ကို Column အသစ်တွေနဲ့ ဆောက်မယ်
    cursor.execute('''CREATE TABLE IF NOT EXISTS repairs 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       name TEXT, phone TEXT, model TEXT, 
                       cost INTEGER, status TEXT, date TEXT,
                       technician TEXT, part_cost INTEGER)''')
    
    # Column အဟောင်းရှိနေရင် အသစ်တွေ ထပ်တိုးမယ် (Migration)
    try:
        cursor.execute("ALTER TABLE repairs ADD COLUMN technician TEXT")
        cursor.execute("ALTER TABLE repairs ADD COLUMN part_cost INTEGER DEFAULT 0")
    except: pass
    conn.commit()
    conn.close()

init_db()

class RepairItem(BaseModel):
    id: Optional[int] = None
    name: str
    phone: str
    model: str
    cost: int
    status: str
    date: str
    technician: Optional[str] = "None"
    part_cost: Optional[int] = 0

@api_app.get("/repairs", response_model=List[RepairItem])
def get_repairs(search: str = ""):
    conn = sqlite3.connect("online_repair.db")
    cursor = conn.cursor()
    if search:
        cursor.execute("SELECT id, name, phone, model, cost, status, date, technician, part_cost FROM repairs WHERE name LIKE ? OR phone LIKE ?", (f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("SELECT id, name, phone, model, cost, status, date, technician, part_cost FROM repairs ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [RepairItem(id=r[0], name=r[1], phone=r[2], model=r[3], cost=r[4], status=r[5], date=r[6], technician=r[7], part_cost=r[8]) for r in rows]

@api_app.post("/repairs")
def add_or_update(item: RepairItem):
    conn = sqlite3.connect("online_repair.db")
    cursor = conn.cursor()
    if item.id:
        cursor.execute("UPDATE repairs SET name=?, phone=?, model=?, cost=?, status=?, date=?, technician=?, part_cost=? WHERE id=?",
                       (item.name, item.phone, item.model, item.cost, item.status, item.date, item.technician, item.part_cost, item.id))
    else:
        cursor.execute("INSERT INTO repairs (name, phone, model, cost, status, date, technician, part_cost) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (item.name, item.phone, item.model, item.cost, item.status, item.date, item.technician, item.part_cost))
    conn.commit()
    conn.close()
    return {"status": "success"}
