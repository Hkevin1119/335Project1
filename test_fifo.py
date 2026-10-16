import os, sys, unittest
from dataclasses import replace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from loader import load_simulation_data
from fifo import schedule_fifo
from models import Donation, Recipient, Volunteer, Status

# All test inputs come from this JSON file (read through loader.load_simulation_data).
SCENARIO_PATH = os.path.join(HERE, "scenario.JSON")


def load_scenario():
    """Load (donations, recipients, volunteers) straight from the JSON file."""
    return load_simulation_data(SCENARIO_PATH)


def _first(items, attr, value):
    for item in items:
        if getattr(item, attr) == value:
            return item
    raise KeyError(f"{value!r} not found in {SCENARIO_PATH}")


def get_donation(donation_id):
    return _first(load_scenario()[0], "donation_id", donation_id)


def get_recipient(recipient_id):
    return _first(load_scenario()[1], "recipient_id", recipient_id)


def get_volunteer(volunteer_id):
    return _first(load_scenario()[2], "volunteer_id", volunteer_id)


def by_id(result):
    return {a.donation_id: a for a in result}


# Plain builders kept only because test_metrics.py imports them. They do NOT feed
# the FIFO/greedy tests, which read everything from scenario.JSON above.
def don(i, qty=10, ftype="meals", expiry=720, ready=600, area="A"):
    return Donation(f"D-{i}", "Donor", ftype, qty, expiry, area, ready, i)

def rec(i="R1", types=("meals",), cap=100, close=1200):
    return Recipient(i, f"Org {i}", frozenset(types), cap, "A", close)

def vol(i="V1", cap=50, area="A", start=480, end=1200, maxp=5):
    return Volunteer(i, cap, area, start, end, maxp)


class TestFifo(unittest.TestCase):
    def test_inputs_come_from_json_file(self):
        self.assertTrue(os.path.isfile(SCENARIO_PATH))
        donations, recipients, volunteers = load_scenario()
        self.assertEqual(len(donations), 8)
        self.assertIn("D-1", [d.donation_id for d in donations])
        self.assertEqual(get_recipient("R1").organization_name, "Community Food Bank")

    def test_normal_match(self):
        [a] = schedule_fifo([get_donation("D-1")], [get_recipient("R1")],
                            [get_volunteer("V1")])
        self.assertEqual(a.status, "ASSIGNED")
        self.assertEqual((a.recipient_id, a.volunteer_id), ("R1", "V1"))
        self.assertIn("because", a.decision_reason)

    def test_no_compatible_food_type(self):
        _, recipients, volunteers = load_scenario()
        [a] = schedule_fifo([get_donation("D-BAD-TYPE")], recipients, volunteers)
        self.assertEqual(a.status, "UNASSIGNED")
        self.assertIn("accepts food type", a.decision_reason)

    def test_insufficient_recipient_capacity(self):
        _, recipients, volunteers = load_scenario()
        [a] = schedule_fifo([get_donation("D-OVER-CAP")], recipients, volunteers)
        self.assertEqual(a.status, "UNASSIGNED")
        self.assertIn("remaining capacity", a.decision_reason)

    def test_no_volunteer_available(self):
        # D-NO-VOL is picked up in "Suburbs"; no volunteer in the JSON covers it.
        _, recipients, volunteers = load_scenario()
        [a] = schedule_fifo([get_donation("D-NO-VOL")], recipients, volunteers)
        self.assertEqual(a.status, "UNASSIGNED")
        self.assertIn("vehicle capacity", a.decision_reason)

    def test_no_volunteer_with_enough_vehicle(self):
        # D-3 (40 units) with only V2 (vehicle holds 30) in its pickup area.
        d3 = replace(get_donation("D-3"), pickup_area=get_volunteer("V2").area)
        [a] = schedule_fifo([d3], [get_recipient("R1")], [get_volunteer("V2")])
        self.assertEqual(a.status, "UNASSIGNED")
        self.assertIn("vehicle capacity", a.decision_reason)

    def test_expired_donation(self):
        _, recipients, volunteers = load_scenario()
        [a] = schedule_fifo([get_donation("D-EXPIRED")], recipients, volunteers)
        self.assertEqual(a.status, "UNASSIGNED")
        self.assertIn("expires", a.decision_reason)

    def test_competing_donations_first_arrival_wins(self):
        # R1 shrunk to 25 units: D-1 (arrival 0) takes it all, D-4 (arrival 3) is
        # rejected even though it is passed in first.
        r1 = replace(get_recipient("R1"), capacity=25)
        result = schedule_fifo([get_donation("D-4"), get_donation("D-1")],
                               [r1], [get_volunteer("V1")])
        res = by_id(result)
        self.assertEqual(res["D-1"].status, Status.ASSIGNED)
        self.assertEqual(res["D-4"].status, Status.UNASSIGNED)

    def test_full_scenario_from_json(self):
        donations, recipients, volunteers = load_scenario()
        result = schedule_fifo(donations, recipients, volunteers)
        res = by_id(result)
        expected = {
            "D-1": Status.ASSIGNED, "D-2": Status.ASSIGNED,
            "D-3": Status.ASSIGNED, "D-4": Status.ASSIGNED,
            "D-EXPIRED": Status.UNASSIGNED, "D-BAD-TYPE": Status.UNASSIGNED,
            "D-OVER-CAP": Status.UNASSIGNED, "D-NO-VOL": Status.UNASSIGNED,
        }
        self.assertEqual({k: v.status for k, v in res.items()}, expected)
        # FIFO processes in arrival order (ties keep their input order).
        self.assertEqual([a.donation_id for a in result],
                         [d.donation_id for d in
                          sorted(donations, key=lambda d: d.arrival_order)])
        self.assertEqual((res["D-2"].recipient_id, res["D-2"].volunteer_id),
                         ("R2", "V2"))

    def test_empty_inputs(self):
        self.assertEqual(schedule_fifo([], [], []), [])
        [a] = schedule_fifo([get_donation("D-1")], [], [])
        self.assertEqual(a.status, "UNASSIGNED")


if __name__ == "__main__":
    unittest.main()
