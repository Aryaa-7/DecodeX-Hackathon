from datetime import datetime, timezone
from pathlib import Path
import csv
from ..repositories.mongodb import store
ROOT=Path(__file__).resolve().parents[3]
def read_csv(name):
    p=ROOT/"data"/name
    if not p.exists(): return []
    with p.open(newline="",encoding="utf-8-sig") as f: return list(csv.DictReader(f))
def load_data():
    courses=read_csv("timetable_courses.csv")
    # Derive academic entities when the optional campus files are absent.
    faculty={}
    sections={}
    rooms=read_csv("CAMPUS-09C_classroom-capacity-2025.csv")
    for c in courses:
        faculty.setdefault(c["faculty_id"],{"faculty_id":c["faculty_id"],"name":c["faculty_id"],"dept":c.get("faculty_dept",c.get("dept","")),"max_weekly_hours":"20","unavailable_slots":""})
        sections.setdefault(c["section_id"],{"section_id":c["section_id"],"dept":c.get("dept",""),"year":c.get("year",""),"students":c.get("section_students",0)})
    if not rooms:
        rooms=[{"room_id":f"R{i:03}","capacity":"100","room_type":"laboratory" if i<=5 else "lecture hall","special_equipment":"network lab" if i<=3 else "none","projector":"true","accessible":"true"} for i in range(1,16)]
    for collection, rows in [("courses",courses),("faculty",list(faculty.values())),("sections",list(sections.values())),("rooms",rooms)]:
        if not store.find(collection):
            for row in rows: store.insert(collection,row)
    if not store.find("users"):
        for u in [{"user_id":"admin","name":"ATMS Administrator","role":"admin","email":"admin@atms.local"},{"user_id":"F007","name":"Dr. Faculty 007","role":"teacher","faculty_id":"F007","phone_number":"+919999900007","department":"CSE"},{"user_id":"F008","name":"Dr. Faculty 008","role":"teacher","faculty_id":"F008","phone_number":"+919999900008","department":"CSE"},{"user_id":"student-cse1","name":"Demo Student","role":"student","section_id":"CSE-1A","email":"student@atms.local"}]: store.insert("users",u)
    return {"courses":len(courses),"faculty":len(faculty),"sections":len(sections),"rooms":len(rooms)}
