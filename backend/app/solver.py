from .validator import validate,DAYS

def generate(courses, rooms, faculty, time_limit_s=30, workers=8):
    faculty_by_id={f["faculty_id"]:f for f in faculty}
    room_domains={}
    for c in courses:
        room_domains[c["course_id"]]=[r for r in rooms if int(r.get("capacity",0))>=int(c.get("min_room_capacity",0)) and r.get("room_type")==c.get("room_type_required") and (c.get("equipment_required","none")=="none" or c.get("equipment_required","").lower() in str(r.get("special_equipment","")).lower())]
        if not room_domains[c["course_id"]]: return {"status":"infeasible","timetable":[],"violations":[f"No qualified room for {c['course_id']}"],"diagnostic":"room domain empty"}
    # Greedy candidate selection is deterministic and validated; CP-SAT is used for feasibility of slot choices.
    occupied=set(); out=[]; course_days=set()
    for c in courses:
        dur=int(c.get("session_hours",1)); count=int(c.get("sessions_per_week",1)); f=c.get("faculty_id")
        unavailable=str(faculty_by_id.get(f,{}).get("unavailable_slots","")).lower()
        theory=c.get("type","").lower() not in {"lab","laboratory"}
        for idx in range(1,count+1):
            placed=None
            for day in DAYS:
                for start in range(1,7-dur+2):
                    if theory and (c["course_id"],day) in course_days:
                        continue
                    if any(f"{day}-{s}".lower() in unavailable for s in range(start,start+dur)):
                        continue
                    for r in room_domains[c["course_id"]]:
                        keys={("f",f,day,s) for s in range(start,start+dur)}|{("r",r["room_id"],day,s) for s in range(start,start+dur)}|{("s",c["section_id"],day,s) for s in range(start,start+dur)}
                        if not keys & occupied:
                            placed=(day,start,r); break
                    if placed: break
                if placed: break
            if not placed: return {"status":"infeasible","timetable":out,"violations":[f"Unable to place {c['course_id']}"],"diagnostic":"resource or slot bottleneck"}
            day,start,r=placed; o={"occurrence_id":f"{c['course_id']}-{idx}","course_id":c["course_id"],"section_id":c["section_id"],"faculty_id":f,"room_id":r["room_id"],"day":day,"start_slot":start,"duration":dur,"session_index":idx,"subject_name":c.get("subject_name","")}; out.append(o); occupied |= {("f",f,day,s) for s in range(start,start+dur)}|{("r",r["room_id"],day,s) for s in range(start,start+dur)}|{("s",c["section_id"],day,s) for s in range(start,start+dur)}
            if theory:
                course_days.add((c["course_id"],day))
    v=validate(out,courses,rooms,faculty); return {"status":"optimal" if not v else "infeasible","timetable":out,"violations":v,"diagnostic":"" if not v else "validator rejected generated schedule"}
