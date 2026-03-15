import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import datetime

# FastAPI ကို စတင်ခြင်း
api_app = FastAPI()

# Database စတင်တည်ဆောက်ခြင်း
def init_db():
    conn = sqlite3.connect("online_repair.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS repairs 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       name TEXT, phone TEXT, model TEXT, cost INTEGER, 
                       status TEXT, date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Data ပုံစံ သတ်မှတ်ခြင်း (Schema)
class RepairItem(BaseModel):
    id: Optional[int] = None
    name: str
    phone: str
    model: str
    cost: int
    status: str
    date: str

# --- API လမ်းကြောင်းများ ---

@api_app.get("/")
def home():
    return {"message": "Mobile Repair API is Running Online!"}

# Data အားလုံးကို ဆွဲထုတ်ခြင်း (သို့မဟုတ် ရှာဖွေခြင်း)
@api_app.get("/repairs", response_model=List[RepairItem])
def get_repairs(search: str = ""):
    conn = sqlite3.connect("online_repair.db")
    cursor = conn.cursor()
    if search:
        query = "SELECT id, name, phone, model, cost, status, date FROM repairs WHERE name LIKE ? OR phone LIKE ?"
        cursor.execute(query, (f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("SELECT id, name, phone, model, cost, status, date FROM repairs ORDER BY id DESC")
    
    rows = cursor.fetchall()
    conn.close()
    
    return [
        RepairItem(id=r[0], name=r[1], phone=r[2], model=r[3], cost=r[4], status=r[5], date=r[6]) 
        for r in rows
    ]

# Data အသစ်ထည့်ခြင်း သို့မဟုတ် Update လုပ်ခြင်း
@api_app.post("/repairs")
def add_or_update(item: RepairItem):
    conn = sqlite3.connect("online_repair.db")
    cursor = conn.cursor()
    
    if item.id:
        # ရှိပြီးသားကို ပြင်မယ်
        cursor.execute("""UPDATE repairs SET name=?, phone=?, model=?, cost=?, status=?, date=? 
                          WHERE id=?""",
                       (item.name, item.phone, item.model, item.cost, item.status, item.date, item.id))
    else:
        # အသစ်ထည့်မယ်
        cursor.execute("""INSERT INTO repairs (name, phone, model, cost, status, date) 
                          VALUES (?, ?, ?, ?, ?, ?)""",
                       (item.name, item.phone, item.model, item.cost, item.status, item.date))
    
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Data saved to cloud database"}

# Server Run ရန် (Local မှာ စမ်းသပ်ရန်အတွက်သာ)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api_app, host="0.0.0.0", port=8000)