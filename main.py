from fastapi import FastAPI, HTTPException, Depends
from tinydb import TinyDB, Query
from typing import List
from datetime import datetime
from pydantic import BaseModel, constr

app = FastAPI()
db = TinyDB('db.json')

class User(BaseModel):
    role: str
    rfid_tag: str
    name: str 
    roll_no: constr(min_length=0, max_length=12)
    is_access: bool

class AccessLog(BaseModel):
    role: str
    rfid_tag: str
    access_time: str
    granted: bool

class AttendanceLog(BaseModel):
    role: str
    rfid_tag: str
    attendance_time: str    

users_table = db.table('users')
access_log_table = db.table('access_log')
attendance_log_table = db.table('attendance_log')

@app.post("/add_users/", response_model=User)
def create_user(user: User):
    existing_user = users_table.search(Query().rfid_tag == user.rfid_tag)
    if existing_user:
        raise HTTPException(status_code=400, detail="RFID tag already exists")
    users_table.insert(user.model_dump())
    return user

@app.get("/users/{rfid_tag}")
def read_user(rfid_tag: str):
    result = users_table.search(Query().rfid_tag == rfid_tag)
    if result:
        return result[0]
    raise HTTPException(status_code=404, detail="User not found")

@app.get("/users/", response_model=List[User])
def read_users():
    return users_table.all()

@app.get("/grant_access/{rfid}")
def grant_access(rfid: str):
    result = users_table.search(Query().rfid_tag == rfid)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    user = result[0]

    if user['is_access']:
        current_time = datetime.now().isoformat()
        access_log_entry = AccessLog(role=user['role'], rfid_tag=rfid, access_time=current_time, granted=True)
        access_log_table.insert(access_log_entry.model_dump())
        return {
            "access": "Granted",
            "message": f"Access granted for user: {user['role']}"
        }
    else:
        current_time = datetime.now().isoformat()
        access_log_entry = AccessLog(role=user['role'], rfid_tag=rfid, access_time=current_time, granted=False)
        access_log_table.insert(access_log_entry.model_dump())
        return {
            "access": "Denied",
            "message": f"Access denied for user: {user['role']} {user['name']}"
        }

@app.get("/name/{id}")
def name(id: int):
    return {"name": users_table.get(doc_id=id)}

@app.get("/logA/{action}")
def logA(action: str):
    id = db.insert({'action': action, 'time': datetime.now().strftime("%d/%m/%Y %H:%M:%S")})
    return {"id": id}

@app.get('/getLog')
def get_log():
    attendance_logs = attendance_log_table.all()
    log_with_names = []

    for log in attendance_logs:
        user = users_table.search(Query().rfid_tag == log['rfid_tag'])
        if user:
            user = user[0]
            log_with_names.append({
                "name": user["name"],
                "rfid_tag": log["rfid_tag"],
                "role": log["role"],
                "attendance_time": log["attendance_time"]
            })

    return log_with_names

@app.get("/access/{id}")
def req_access(id: str):
    return {"access": "Granted"}

@app.post("/log_attendance/{rfid}")
def log_attendance(rfid: str):
    result = users_table.search(Query().rfid_tag == rfid)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    user = result[0]
    current_time = datetime.now().isoformat()
    
    attendance_log_entry = AttendanceLog(role=user['role'], rfid_tag=rfid, attendance_time=current_time)
    attendance_log_table.insert(attendance_log_entry.model_dump())
    
    return {
        "message": f"Attendance logged for user: {user['role']}"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)