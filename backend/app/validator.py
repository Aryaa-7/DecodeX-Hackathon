from collections import defaultdict
DAYS=["Mon","Tue","Wed","Thu","Fri"]
def _slots(o): return [(o.get("day"),s) for s in range(o.get("start_slot",0),o.get("start_slot",0)+o.get("duration",1))]
def validate(timetable, courses=None, rooms=None, faculty=None):
    courses={c["course_id"]:c for c in (courses or [])}; rooms={r["room_id"]:r for r in (rooms or [])}; faculty={f["faculty_id"]:f for f in (faculty or [])}; violations=[]
    seen=defaultdict(list)
    for o in timetable:
        c=courses.get(o.get("course_id"),o); slots=_slots(o)
        for key in [("faculty",o.get("faculty_id")),("room",o.get("room_id")),("section",o.get("section_id"))]:
            if key[1]:
                for d,s in slots:
                    if seen[(key[0],key[1],d,s)]: violations.append(f"{key[0].title()} {key[1]} is double-booked on {d}-{s}.")
                    seen[(key[0],key[1],d,s)].append(o)
        r=rooms.get(o.get("room_id"),{})
        if r and int(r.get("capacity",0))<int(c.get("min_room_capacity",0)): violations.append(f"Room {o.get('room_id')} lacks capacity.")
        if r and c.get("room_type_required") and r.get("room_type")!=c.get("room_type_required"): violations.append(f"Room {o.get('room_id')} has wrong type.")
        req=(c.get("equipment_required") or "none").lower(); eq=str(r.get("special_equipment","")).lower()
        if req not in ("","none") and req not in eq: violations.append(f"Room {o.get('room_id')} does not support required equipment.")
        f=faculty.get(o.get("faculty_id"),{}); unavailable=str(f.get("unavailable_slots","")).lower()
        if any(f"{d}-{s}".lower() in unavailable for d,s in slots): violations.append(f"Faculty {o.get('faculty_id')} is unavailable on {slots[0][0]}-{slots[0][1]}.")
    groups=defaultdict(list)
    for o in timetable:
        g=courses.get(o.get("course_id"),o).get("elective_group")
        if g: groups[g].append(o)
    for g, rows in groups.items():
        for i in range(max([x.get("session_index",1) for x in rows] or [0])):
            pos={(x.get("day"),x.get("start_slot")) for x in rows if x.get("session_index",1)==i+1}
            if len(pos)>1: violations.append(f"Elective group {g} has misaligned session {i+1}.")
    return list(dict.fromkeys(violations))
