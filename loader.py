import json
from models import Donation, Recipient, Volunteer


def load_simulation_data(filepath: str):
    #Loads recipients, volunteers, and donations from a master JSON file
    with open(filepath, "r") as f:
        data = json.load(f)

    # Convert recipient dictionaries into Recipient objects (converting list to frozenset)

    recipients = [
        Recipient(
            recipient_id=r["recipient_id"],
            organization_name=r["organization_name"],
            accepted_types=frozenset(r["accepted_types"]),
            capacity=r["capacity"],
            area=r["area"],
            closing_time=r["closing_time"]
        )
        for r in data["recipients"]
    ]

    # Convert volunteer dictionaries into Volunteer objects
    volunteers = [
        Volunteer(**v) for v in data["volunteers"]
    ]

    # Convert donation dictionaries into Donation objects
    donations = [
        Donation(**d) for d in data["donations"]
    ]

    return donations, recipients, volunteers