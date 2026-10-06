from pydantic import BaseModel, Field
from typing import Optional, Any
class User(BaseModel): user_id:str; name:str; role:str; phone_number:str=""; email:str=""; department:str=""; section_id:Optional[str]=None; faculty_id:Optional[str]=None
class Move(BaseModel): occurrence_id:str; day:str; start_slot:int; room_id:Optional[str]=None; faculty_id:Optional[str]=None
class Event(BaseModel): type:str; id:str; day:str; slots:list[int]
class ChatMessage(BaseModel): ciphertext:str; iv:str
class ChatCreate(BaseModel): participant_id:str
class NotificationConfig(BaseModel): minutes_before:int=Field(10,ge=0,le=120)
