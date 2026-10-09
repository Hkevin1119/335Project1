import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_fifo import don, rec, vol
from fifo import schedule_fifo
from greedy import schedule_greedy, priority_key
from models import Status


def by_id(result):
    return {a.donation_id: a for a in result}


class TestGreedy(unittest.TestCase):
    def test_priority_key_order(self):
        a = don(1, expiry=700)            # shelf life 100
        b = don(2, expiry=650)            # shelf life 50  -> first
        c = don(3, qty=20, expiry=700)    # shelf life 100, bigger qty -> before a
        d = don(4, expiry=700)            # tie with a, arrived later -> after a
        order = sorted([a, b, c, d], key=priority_key)
        self.assertEqual([x.donation_id for x in order], ["D-2", "D-3", "D-1", "D-4"])

    def test_fifo_and_greedy_differ(self):
        # One slot of capacity. D-1 arrives first but is not urgent; D-2 expires soon.
        donations = [don(1, expiry=900), don(2, expiry=640)]
        recipients, volunteers = [rec(cap=10)], [vol()]
        f = by_id(schedule_fifo(donations, recipients, volunteers))
        g = by_id(schedule_greedy(donations, recipients, volunteers))
        self.assertEqual((f["D-1"].status, f["D-2"].status),
                         (Status.ASSIGNED, Status.UNASSIGNED))
        self.assertEqual((g["D-1"].status, g["D-2"].status),
                         (Status.UNASSIGNED, Status.ASSIGNED))

    def test_ordering_explanation_present(self):
        donations = [don(1, expiry=900), don(2, expiry=640)]
        g = by_id(schedule_greedy(donations, [rec(cap=100)], [vol()]))
        self.assertIn("considered after D-2", g["D-1"].decision_reason)
        self.assertIn("less remaining shelf life", g["D-1"].decision_reason)
        self.assertNotIn("considered after", g["D-2"].decision_reason)

    def test_quantity_breaks_shelf_life_tie(self):
        donations = [don(1, qty=10), don(2, qty=30)]   # same shelf life
        g = by_id(schedule_greedy(donations, [rec(cap=30)], [vol()]))
        self.assertEqual(g["D-2"].status, Status.ASSIGNED)
        self.assertEqual(g["D-1"].status, Status.UNASSIGNED)

    def test_starvation_case(self):
        # Fairness discussion: a large, long-lived donation that arrived FIRST is
        # starved because a stream of urgent small donations keeps claiming capacity.
        big = don(1, qty=50, expiry=1200)
        urgent = [don(i, qty=10, expiry=700) for i in range(2, 7)]  # 5 x 10 units
        g = by_id(schedule_greedy([big] + urgent, [rec(cap=50)], [vol()]))
        self.assertEqual(g["D-1"].status, Status.UNASSIGNED)
        self.assertTrue(all(g[f"D-{i}"].status == Status.ASSIGNED for i in range(2, 7)))
        self.assertIn("considered after", g["D-1"].decision_reason)

    def test_empty_inputs(self):
        self.assertEqual(schedule_greedy([], [], []), [])


if __name__ == "__main__":
    unittest.main()
