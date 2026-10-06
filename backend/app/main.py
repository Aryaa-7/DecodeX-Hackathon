from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
from uuid import uuid4
from .repositories.mongodb import store
from .data.loader import load_data
from .solver import generate
from .validator import validate
from .schemas import Move, Event, ChatMessage, ChatCreate, NotificationConfig
app=FastAPI(title="ATMS MVP",version="1.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])
@app.on_event("startup")
def startup(): load_data()
def user(x_user_id: str=Header("student-cse1")):
    u=store.one("users",{"user_id":x_user_id})
    if not u: raise HTTPException(401,"Unknown demo profile")
    return u
def role(*roles):
    def dep(u=Depends(user)):
        if u["role"] not in roles: raise HTTPException(403,"Insufficient role")
        return u
    return dep
@app.get("/health")
def health(): return {"ok":True,"mongodb":store.mongo}
@app.get("/users")
def users(): return store.find("users")
@app.get("/me")
def me(u=Depends(user)): return u
@app.post("/generate")
def gen(u=Depends(role("admin")), time_limit_s:int=30):
    result=generate(store.find("courses"),store.find("rooms"),store.find("faculty"),time_limit_s)
    if result["status"]!="infeasible" and not result["violations"]:
        tid=str(uuid4()); doc={"timetable_id":tid,"occurrences":result["timetable"],"created_at":datetime.now(timezone.utc).isoformat()}; store.insert("timetables",doc); store.replace("app_state",{"key":"current_timetable"},{"key":"current_timetable","timetable_id":tid}); result["timetable_id"]=tid
    result.update({"hard_violations":len(result["violations"]),"soft_score":0,"room_utilisation":0,"legacy_double_booked_slots":0,"generation_duration_ms":0}); return result
@app.get("/timetable")
def timetable(view:str="section",id:str="",u=Depends(user)):
    t=store.one("app_state",{"key":"current_timetable"}); rows=store.one("timetables",{"timetable_id":t.get("timetable_id")}) if t else None; occ=(rows or {}).get("occurrences",[])
    if u["role"]=="teacher" and view=="faculty" and id!=u.get("faculty_id"): raise HTTPException(403,"Own timetable only")
    if u["role"]=="student" and view=="section" and id!=u.get("section_id"): raise HTTPException(403,"Own section only")
    key={"section":"section_id","faculty":"faculty_id","room":"room_id"}.get(view)
    return [o for o in occ if not key or not id or o.get(key)==id]
@app.get("/vacancy/rooms")
def vacancy(day:str,slot:int,duration:int=1,minCapacity:int=0,type:str="",equipment:str="none",accessible:bool=False):
    t=store.one("app_state",{"key":"current_timetable"}); current=store.one("timetables",{"timetable_id":t.get("timetable_id")}) if t else {}; busy={o["room_id"] for o in current.get("occurrences",[]) if o.get("day")==day and o.get("start_slot",0)<=slot<o.get("start_slot",0)+o.get("duration",1)}
    return [r for r in store.find("rooms") if r["room_id"] not in busy and int(r.get("capacity",0))>=minCapacity and (not type or r.get("room_type")==type) and (equipment=="none" or equipment.lower() in str(r.get("special_equipment","")).lower()) and (not accessible or str(r.get("accessible")).lower()=="true")]
@app.post("/validate-move")
def validate_move(m:Move,u=Depends(user)):
    t=store.one("app_state",{"key":"current_timetable"}); doc=store.one("timetables",{"timetable_id":t.get("timetable_id")}) if t else None
    rows=[dict(x) for x in (doc or {}).get("occurrences",[])]; target=next((x for x in rows if x["occurrence_id"]==m.occurrence_id),None)
    if not target: raise HTTPException(404,"Occurrence not found")
    target.update({"day":m.day,"start_slot":m.start_slot});
    v=validate(rows,store.find("courses"),store.find("rooms"),store.find("faculty")); return {"valid":not v,"violations":v}
@app.post("/move")
def move(m:Move,u=Depends(role("admin","teacher"))):
    check=validate_move(m,u)
    if not check["valid"]: raise HTTPException(409,{"violations":check["violations"]})
    t=store.one("app_state",{"key":"current_timetable"}); doc=store.one("timetables",{"timetable_id":t["timetable_id"]}); store.insert("undo_stack",{"timetable_id":t["timetable_id"],"occurrences":doc["occurrences"]}); rows=doc["occurrences"]
    for x in rows:
        if x["occurrence_id"]==m.occurrence_id: x.update({"day":m.day,"start_slot":m.start_slot})
    store.update("timetables",{"timetable_id":t["timetable_id"]},{"occurrences":rows}); return {"ok":True}
@app.post("/undo")
def undo(u=Depends(role("admin","teacher"))):
    stack=store.find("undo_stack"); t=store.one("app_state",{"key":"current_timetable"})
    if not stack or not t: raise HTTPException(404,"Nothing to undo")
    old=stack[-1]; store.update("timetables",{"timetable_id":t["timetable_id"]},{"occurrences":old["occurrences"]}); store.delete("undo_stack",{"timetable_id":t["timetable_id"]}); return {"ok":True}
@app.get("/conflicts")
def conflicts(u=Depends(user)): return store.find("conflicts",{"status":{"$ne":"resolved"}}) if store.mongo else store.find("conflicts")
@app.post("/events")
def events(e:Event,u=Depends(role("admin","teacher"))):
    affected=[o for o in (timetable("section","",u)) if (e.type=="FACULTY_ABSENT" and o.get("faculty_id")==e.id) or (e.type=="ROOM_CLOSED" and o.get("room_id")==e.id)]
    event={"event_id":str(uuid4()),**e.model_dump(),"affected_classes":affected}; store.insert("events",event); store.insert("proposals",{"proposal_id":str(uuid4()),"strategy":"L1","moves_count":len(affected),"affected_classes":affected,"explanation":"Move to nearest qualified free slot","cost":len(affected)}); return {"event":event,"proposals":store.find("proposals")}
@app.get("/notifications")
def notifications(recipient_type:str="",recipient_id:str="",u=Depends(user)): return [n for n in store.find("notifications") if (not recipient_id or n.get("recipient_id")==recipient_id)]
@app.post("/notifications/{nid}/read")
def read(nid:str,u=Depends(user)):
    n=store.one("notifications",{"notification_id":nid});
    if not n: raise HTTPException(404,"Notification not found")
    if n.get("recipient_id")!=u["user_id"]: raise HTTPException(403,"Forbidden")
    store.update("notifications",{"notification_id":nid},{"read":True}); return {"ok":True}
@app.post("/notifications/read-all")
def read_all(u=Depends(user)):
    for n in store.find("notifications",{"recipient_id":u["user_id"]}): store.update("notifications",{"notification_id":n["notification_id"]},{"read":True})
    return {"ok":True}
@app.get("/notifications/config")
def config(): return store.one("notification_config",{"key":"default"}) or {"key":"default","minutes_before":10}
@app.post("/notifications/config")
def set_config(c:NotificationConfig,u=Depends(user)): store.replace("notification_config",{"key":"default"},{"key":"default",**c.model_dump()}); return config()
@app.post("/notifications/demo-time")
def demo_time(value:dict,u=Depends(role("admin"))): store.replace("app_state",{"key":"simulated_time"},{"key":"simulated_time",**value}); return value
@app.post("/chat/conversations")
def chat_create(c:ChatCreate,u=Depends(role("teacher"))):
    other=store.one("users",{"user_id":c.participant_id,"role":"teacher"});
    if not other: raise HTTPException(404,"Teacher not found")
    found=next((x for x in store.find("chat_conversations") if set(x["participants"])=={u["user_id"],c.participant_id}),None)
    return found or store.insert("chat_conversations",{"conversation_id":str(uuid4()),"participants":[u["user_id"],c.participant_id]})
@app.get("/chat/conversations")
def chats(u=Depends(role("teacher"))): return [x for x in store.find("chat_conversations") if u["user_id"] in x.get("participants",[])]
def conversation(cid,u):
    c=store.one("chat_conversations",{"conversation_id":cid})
    if not c or u["user_id"] not in c.get("participants",[]): raise HTTPException(403,"Conversation access denied")
    return c
@app.get("/chat/{cid}/messages")
def messages(cid:str,u=Depends(role("teacher"))): conversation(cid,u); return store.find("chat_messages",{"conversation_id":cid})
@app.post("/chat/{cid}/messages")
def send(cid:str,m:ChatMessage,u=Depends(role("teacher"))): conversation(cid,u); return store.insert("chat_messages",{"message_id":str(uuid4()),"conversation_id":cid,"sender_id":u["user_id"],**m.model_dump()})
