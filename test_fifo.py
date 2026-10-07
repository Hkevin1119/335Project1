import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Donation, Recipient, Volunteer
from fifo import schedule_fifo


def don(i, qty=10, ftype="meals", expiry=720, ready=600, area="A"):
    return Donation(f"D-{i}", "Donor", ftype, qty, expiry, area, ready, i)

def rec(i="R1", types=("meals",), cap=100, close=1200):
    return Recipient(i, f"Org {i}", frozenset(types), cap, "A", close)

def vol(i="V1", cap=50, area="A", start=480, end=1200, maxp=5):
    return Volunteer(i, cap, area, start, end, maxp)


class TestFifo(unittest.TestCase):
    def test_normal_match(self):
        [a] = schedule_fifo([don(1)], [rec()], [vol()])
        self.assertEqual(a.status, "ASSIGNED")
        self.assertEqual((a.recipient_id, a.volunteer_id), ("R1", "V1"))
        self.assertIn("because", a.decision_reason)

    def test_no_compatible_food_type(self):
        [a] = schedule_fifo([don(1, ftype="produce")], [rec()], [vol()])
        self.assertEqual(a.status, "UNASSIGNED")
        self.assertIn("accepts food type", a.decision_reason)

    def test_insufficient_recipient_capacity(self):
        [a] = schedule_fifo([don(1, qty=10)], [rec(cap=5)], [vol()])
        self.assertEqual(a.status, "UNASSIGNED")
        self.assertIn("remaining capacity", a.decision_reason)

    def test_no_volunteer_with_enough_vehicle(self):
        [a] = schedule_fifo([don(1, qty=40)], [rec()], [vol(cap=20)])
        self.assertEqual(a.status, "UNASSIGNED")
        self.assertIn("vehicle capacity", a.decision_reason)

    def test_expired_donation(self):
        [a] = schedule_fifo([don(1, ready=700, expiry=705)], [rec()], [vol()])
        self.assertEqual(a.status, "UNASSIGNED")
        self.assertIn("expires", a.decision_reason)

    def test_competing_donations_first_arrival_wins(self):
        # Only 10 units of capacity: D-1 (arrived first) takes it, D-2 is rejected.
        result = schedule_fifo([don(2), don(1)], [rec(cap=10)], [vol()])
        by_id = {a.donation_id: a for a in result}
        self.assertEqual(by_id["D-1"].status, "ASSIGNED")
        self.assertEqual(by_id["D-2"].status, "UNASSIGNED")

    def test_empty_inputs(self):
        self.assertEqual(schedule_fifo([], [], []), [])
        [a] = schedule_fifo([don(1)], [], [])
        self.assertEqual(a.status, "UNASSIGNED")


if __name__ == "__main__":
    unittest.main()
