import sqlite3
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

api_app = FastAPI()

def auto_fix_db():
    """Database Table နှင့် Column များကို အလိုအလျောက် စစ်ဆေးပြင်ဆင်ပေးခြင်း"""
    conn = sqlite3.connect("online_repair.db")
    cursor = conn.cursor()
    
    # ၁။ Table အခြေခံ ဆောက်ခြင်း
    cursor.execute('''CREATE TABLE IF NOT EXISTS repairs 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       name TEXT, phone TEXT, model TEXT, 
                       cost INTEGER, status TEXT, date TEXT)''')
    
    # ၂။ လိုအပ်သော Column များ ရှိမရှိ စစ်ဆေးခြင်း
    existing_columns = [row[1] for row in cursor.execute("PRAGMA table_info(repairs)")]
    
    if "technician" not in existing_columns:
        print("Adding technician column...")
        cursor.execute("ALTER TABLE repairs ADD COLUMN technician TEXT DEFAULT 'None'")
    
    if "part_cost" not in existing_columns:
        print("Adding part_cost column...")
        cursor.execute("ALTER TABLE repairs ADD COLUMN part_cost INTEGER DEFAULT 0")
        
    conn.commit()
    conn.close()

# Server စတင်ချိန်တွင် Database Fix ကို ခေါ်ယူမည်
auto_fix_db()

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

# --- ၁။ စာရင်းများ ဆွဲယူရန် (GET) ---
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
    return [RepairItem(id=r[0], name=r[1], phone=r[2], model=r[3], cost=r[4], status=r[5], date=r[6], technician=r[7] if r[7] else "None", part_cost=r[8] if r[8] else 0) for r in rows]

# --- ၂။ စာရင်းအသစ်ထည့်ရန် သို့မဟုတ် ပြင်ရန် (POST) ---
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

# --- ၃။ စာရင်းဖျက်ရန် (DELETE) - ဒါကို အသစ်ပေါင်းထည့်ထားပါတယ် ---
@api_app.delete("/repairs/{id}")
def delete_repair(id: int):
    conn = sqlite3.connect("online_repair.db")
    cursor = conn.cursor()
    
    # ID ရှိမရှိ အရင်စစ်မည်
    cursor.execute("SELECT id FROM repairs WHERE id = ?", (id,))
    item = cursor.fetchone()
    
    if item:
        cursor.execute("DELETE FROM repairs WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"Job {id} deleted successfully"}
    else:
        conn.close()
        return {"status": "error", "message": "Item not found"}, 404

if __name__ == "__main__":
    uvicorn.run(api_app, host="0.0.0.0", port=8000)
