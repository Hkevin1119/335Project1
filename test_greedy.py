import os, sys, unittest
from dataclasses import replace

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Inputs come from the JSON file via the helpers in test_fifo (which call
# loader.load_simulation_data on scenario.JSON).
from test_fifo import (load_scenario, get_donation, get_recipient,
                       get_volunteer, by_id)
from fifo import schedule_fifo
from greedy import schedule_greedy, priority_key
from models import Status


class TestGreedy(unittest.TestCase):
    def test_priority_key_order(self):
        base = get_donation("D-4")                   # JSON: ready 620, expiry 710 -> 90 min
        a = replace(base, donation_id="D-A")                                    # 90 min
        b = replace(base, donation_id="D-B", expiry_time=670, arrival_order=1)  # 50 min -> first
        c = replace(base, donation_id="D-C", quantity=30, arrival_order=2)      # 90 min, bigger qty -> before a
        d = replace(base, donation_id="D-D", arrival_order=3)                   # tie with a, later -> after a
        order = sorted([a, b, c, d], key=priority_key)
        self.assertEqual([x.donation_id for x in order], ["D-B", "D-C", "D-A", "D-D"])

    def test_priority_order_of_json_donations(self):
        donations, _, _ = load_scenario()
        order = [d.donation_id for d in sorted(donations, key=priority_key)][:5]
        self.assertEqual(order, ["D-EXPIRED", "D-2", "D-4", "D-1", "D-3"])

    def test_fifo_and_greedy_differ(self):
        # R1 shrunk to 25 units. D-1 (25 units) arrives first but is less urgent than
        # D-4 (20 units, expires sooner), so only one of them can be placed.
        donations = [get_donation("D-1"), get_donation("D-4")]
        recipients = [replace(get_recipient("R1"), capacity=25)]
        volunteers = [get_volunteer("V1")]
        f = by_id(schedule_fifo(donations, recipients, volunteers))
        g = by_id(schedule_greedy(donations, recipients, volunteers))
        self.assertEqual((f["D-1"].status, f["D-4"].status),
                         (Status.ASSIGNED, Status.UNASSIGNED))
        self.assertEqual((g["D-1"].status, g["D-4"].status),
                         (Status.UNASSIGNED, Status.ASSIGNED))

    def test_full_scenario_from_json(self):
        donations, recipients, volunteers = load_scenario()
        g = schedule_greedy(donations, recipients, volunteers)
        res = by_id(g)
        # Most urgent first: the expired donation leads, then D-2, D-4, D-1, D-3.
        self.assertEqual([a.donation_id for a in g][:5],
                         ["D-EXPIRED", "D-2", "D-4", "D-1", "D-3"])
        expected = {
            "D-1": Status.ASSIGNED, "D-2": Status.ASSIGNED,
            "D-3": Status.ASSIGNED, "D-4": Status.ASSIGNED,
            "D-EXPIRED": Status.UNASSIGNED, "D-BAD-TYPE": Status.UNASSIGNED,
            "D-OVER-CAP": Status.UNASSIGNED, "D-NO-VOL": Status.UNASSIGNED,
        }
        self.assertEqual({k: v.status for k, v in res.items()}, expected)
        # Same donations, different order -> different pickup times than FIFO.
        f = by_id(schedule_fifo(donations, recipients, volunteers))
        self.assertNotEqual(f["D-1"].scheduled_time, res["D-1"].scheduled_time)

    def test_ordering_explanation_present(self):
        donations, recipients, volunteers = load_scenario()
        g = by_id(schedule_greedy(donations, recipients, volunteers))
        self.assertIn("considered after D-2", g["D-1"].decision_reason)
        self.assertIn("less remaining shelf life", g["D-1"].decision_reason)
        self.assertNotIn("considered after", g["D-2"].decision_reason)

    def test_quantity_breaks_shelf_life_tie(self):
        # D-1 is edited so it has the same shelf life as D-4 (90 min) but a larger
        # quantity (25 vs 20); R1 has room for only one of them.
        d1 = replace(get_donation("D-1"), expiry_time=690)
        d4 = get_donation("D-4")
        self.assertEqual(d1.remaining_shelf_life, d4.remaining_shelf_life)
        g = by_id(schedule_greedy([d4, d1],
                                  [replace(get_recipient("R1"), capacity=25)],
                                  [get_volunteer("V1")]))
        self.assertEqual(g["D-1"].status, Status.ASSIGNED)
        self.assertEqual(g["D-4"].status, Status.UNASSIGNED)

    def test_starvation_case(self):
        # Fairness discussion: a large, long-lived donation (D-3, arrived first) is
        # starved because a stream of urgent small donations claims all capacity.
        big = get_donation("D-3")                                   # 40 units
        urgent = [replace(get_donation("D-4"), donation_id=f"D-U{i}",
                          quantity=10, arrival_order=10 + i) for i in range(4)]
        g = by_id(schedule_greedy([big] + urgent,
                                  [replace(get_recipient("R1"), capacity=40)],
                                  [get_volunteer("V1")]))
        self.assertEqual(g["D-3"].status, Status.UNASSIGNED)
        self.assertTrue(all(g[f"D-U{i}"].status == Status.ASSIGNED for i in range(4)))
        self.assertIn("considered after", g["D-3"].decision_reason)

    def test_empty_inputs(self):
        self.assertEqual(schedule_greedy([], [], []), [])


if __name__ == "__main__":
    unittest.main()
