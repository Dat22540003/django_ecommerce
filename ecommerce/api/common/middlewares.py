from pymongo import monitoring
from datetime import datetime


class TimestampMiddleware(monitoring.CommandListener):
    def started(self, event):
        if event.command_name in ["insert", "update"]:
            now = datetime.utcnow()
            if event.command_name == "insert":
                for doc in event.command["documents"]:
                    doc["created_at"] = now
                    doc["updated_at"] = now
            elif event.command_name == "update":
                event.command["updates"][0]["u"]["$currentDate"] = {
                    "updated_at": True}


monitoring.register(TimestampMiddleware())
