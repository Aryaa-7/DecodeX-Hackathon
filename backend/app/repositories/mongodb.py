from datetime import datetime, timezone
from typing import Any
from pymongo import MongoClient, ASCENDING, DESCENDING
from ..config import settings

class Store:
    def __init__(self):
        self.memory = {}
        self.client = None
        try:
            self.client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=1200)
            self.client.admin.command("ping")
            self.db = self.client[settings.mongodb_database]
            self.mongo = True
            self.ensure_indexes()
        except Exception:
            self.db = None; self.mongo = False
    def ensure_indexes(self):
        for c, keys in {"users":[("role",ASCENDING),("faculty_id",ASCENDING),("section_id",ASCENDING)],"timetables":[("created_at",DESCENDING)],"notifications":[("recipient_id",ASCENDING),("occurrence_id",ASCENDING)],"conflicts":[("status",ASCENDING)],"chat_conversations":[("participants",ASCENDING)],"chat_messages":[("conversation_id",ASCENDING),("created_at",ASCENDING)]}.items():
            try: self.db[c].create_index(keys)
            except Exception: pass
    def find(self, collection, query=None):
        query=query or {}
        if self.mongo: return list(self.db[collection].find(query, {"_id":0}))
        return [x for x in self.memory.get(collection,[]) if all(x.get(k)==v for k,v in query.items())]
    def one(self, collection, query):
        rows=self.find(collection,query); return rows[0] if rows else None
    def insert(self, collection, doc):
        doc=dict(doc); doc.setdefault("created_at",datetime.now(timezone.utc).isoformat())
        if self.mongo: self.db[collection].insert_one(doc)
        else: self.memory.setdefault(collection,[]).append(doc)
        return doc
    def replace(self, collection, query, doc):
        if self.mongo: self.db[collection].replace_one(query,doc,upsert=True)
        else:
            rows=self.memory.setdefault(collection,[]); old=self.one(collection,query)
            if old: rows[rows.index(old)]=doc
            else: rows.append(doc)
    def update(self, collection, query, changes):
        if self.mongo: self.db[collection].update_one(query,{"$set":changes})
        else:
            row=self.one(collection,query)
            if row: row.update(changes)
    def delete(self, collection, query):
        if self.mongo: self.db[collection].delete_many(query)
        else: self.memory[collection]=[x for x in self.memory.get(collection,[]) if not all(x.get(k)==v for k,v in query.items())]
store=Store()
