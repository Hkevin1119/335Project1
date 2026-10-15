import os
import sys
import unittest

sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    ),
)

from fifo import schedule_fifo
from greedy import schedule_greedy
from metrics import calculate_metrics
from models import Status
from test_fifo import don, rec, vol


class TestMetrics(unittest.TestCase):
    def test_normal_metrics(self):
        donations = [
            don(1, qty=10, expiry=700),
            don(2, qty=20, expiry=900),
        ]
        recipients = [rec(cap=30)]
        volunteers = [vol(maxp=2)]

        assignments = schedule_fifo(
            donations,
            recipients,
            volunteers,
        )
        metrics = calculate_metrics(
            donations,
            assignments,
            recipients,
            volunteers,
        )

        self.assertEqual(metrics.donations_received, 2)
        self.assertEqual(metrics.donations_assigned, 2)
        self.assertEqual(metrics.donations_unassigned, 0)
        self.assertEqual(metrics.food_quantity_rescued, 30)
        self.assertEqual(metrics.food_quantity_at_risk, 0)
        self.assertEqual(metrics.urgent_donations_received, 1)
        self.assertEqual(metrics.urgent_donations_assigned, 1)
        self.assertEqual(metrics.urgent_rescue_rate, 1.0)
        self.assertEqual(
            metrics.recipient_capacity_utilization,
            1.0,
        )
        self.assertEqual(
            metrics.volunteer_capacity_utilization,
            1.0,
        )

    def test_unassigned_quantity_is_at_risk(self):
        donations = [
            don(1, qty=10),
            don(2, qty=20),
        ]
        recipients = [rec(cap=10)]
        volunteers = [vol(maxp=2)]

        assignments = schedule_fifo(
            donations,
            recipients,
            volunteers,
        )
        metrics = calculate_metrics(
            donations,
            assignments,
            recipients,
            volunteers,
        )

        self.assertEqual(metrics.donations_assigned, 1)
        self.assertEqual(metrics.donations_unassigned, 1)
        self.assertEqual(metrics.food_quantity_rescued, 10)
        self.assertEqual(metrics.food_quantity_at_risk, 20)

    def test_no_urgent_donations(self):
        donations = [
            don(1, expiry=900),
        ]
        recipients = [rec()]
        volunteers = [vol()]

        assignments = schedule_fifo(
            donations,
            recipients,
            volunteers,
        )
        metrics = calculate_metrics(
            donations,
            assignments,
            recipients,
            volunteers,
        )

        self.assertEqual(metrics.urgent_donations_received, 0)
        self.assertEqual(metrics.urgent_donations_assigned, 0)
        self.assertEqual(metrics.urgent_rescue_rate, 0.0)

    def test_empty_input_has_zero_metrics(self):
        metrics = calculate_metrics([], [], [], [])

        self.assertEqual(metrics.donations_received, 0)
        self.assertEqual(metrics.donations_assigned, 0)
        self.assertEqual(metrics.donations_unassigned, 0)
        self.assertEqual(metrics.food_quantity_rescued, 0)
        self.assertEqual(metrics.food_quantity_at_risk, 0)
        self.assertEqual(metrics.urgent_rescue_rate, 0.0)
        self.assertEqual(
            metrics.recipient_capacity_utilization,
            0.0,
        )
        self.assertEqual(
            metrics.volunteer_capacity_utilization,
            0.0,
        )

    def test_fifo_and_greedy_use_same_input(self):
        donations = [
            don(1, qty=10, expiry=900),
            don(2, qty=10, expiry=640),
        ]
        recipients = [rec(cap=10)]
        volunteers = [vol(maxp=1)]

        fifo_results = schedule_fifo(
            donations,
            recipients,
            volunteers,
        )
        greedy_results = schedule_greedy(
            donations,
            recipients,
            volunteers,
        )

        fifo_metrics = calculate_metrics(
            donations,
            fifo_results,
            recipients,
            volunteers,
        )
        greedy_metrics = calculate_metrics(
            donations,
            greedy_results,
            recipients,
            volunteers,
        )

        fifo_by_id = {
            a.donation_id: a
            for a in fifo_results
        }
        greedy_by_id = {
            a.donation_id: a
            for a in greedy_results
        }

        self.assertEqual(
            fifo_by_id["D-1"].status,
            Status.ASSIGNED,
        )
        self.assertEqual(
            greedy_by_id["D-2"].status,
            Status.ASSIGNED,
        )
        self.assertEqual(fifo_metrics.donations_assigned, 1)
        self.assertEqual(greedy_metrics.donations_assigned, 1)
        self.assertEqual(fifo_metrics.food_quantity_rescued, 10)
        self.assertEqual(greedy_metrics.food_quantity_rescued, 10)
        self.assertEqual(fifo_metrics.urgent_rescue_rate, 0.0)
        self.assertEqual(greedy_metrics.urgent_rescue_rate, 1.0)

    def test_zero_capacity_denominators(self):
        donations = [don(1)]
        assignments = schedule_fifo(donations, [], [])

        metrics = calculate_metrics(
            donations,
            assignments,
            [],
            [],
        )

        self.assertEqual(
            metrics.recipient_capacity_utilization,
            0.0,
        )
        self.assertEqual(
            metrics.volunteer_capacity_utilization,
            0.0,
        )


if __name__ == "__main__":
    unittest.main()
