import json
from datetime import date

def build_protocol(title, participants, summaries, actions):
    protocol = {
        "title": title,
        "date": str(date.today()),
        "participants": participants,
        "body": summaries,
        "action_items": json.loads(actions)
    }
    return protocol
