from dataclasses import dataclass

from models import Status


URGENT_THRESHOLD_MINUTES = 120


@dataclass(frozen=True)
class Metrics:
    donations_received: int
    donations_assigned: int
    donations_unassigned: int
    food_quantity_rescued: int
    food_quantity_at_risk: int
    urgent_donations_received: int
    urgent_donations_assigned: int
    urgent_rescue_rate: float
    recipient_capacity_utilization: float
    volunteer_capacity_utilization: float


def calculate_metrics(
    donations,
    assignments,
    recipients,
    volunteers,
    urgent_threshold=URGENT_THRESHOLD_MINUTES,
):
    donations_by_id = {d.donation_id: d for d in donations}
    assigned = [a for a in assignments if a.status == Status.ASSIGNED]
    unassigned = [a for a in assignments if a.status == Status.UNASSIGNED]

    rescued = sum(
        donations_by_id[a.donation_id].quantity
        for a in assigned
    )
    at_risk = sum(
        donations_by_id[a.donation_id].quantity
        for a in unassigned
    )

    urgent_ids = {
        d.donation_id
        for d in donations
        if d.remaining_shelf_life <= urgent_threshold
    }
    urgent_assigned = sum(
        a.donation_id in urgent_ids
        for a in assigned
    )

    recipient_capacity = sum(r.capacity for r in recipients)
    volunteer_pickup_capacity = sum(v.max_pickups for v in volunteers)

    return Metrics(
        donations_received=len(donations),
        donations_assigned=len(assigned),
        donations_unassigned=len(unassigned),
        food_quantity_rescued=rescued,
        food_quantity_at_risk=at_risk,
        urgent_donations_received=len(urgent_ids),
        urgent_donations_assigned=urgent_assigned,
        urgent_rescue_rate=(
            urgent_assigned / len(urgent_ids)
            if urgent_ids else 0.0
        ),
        recipient_capacity_utilization=(
            rescued / recipient_capacity
            if recipient_capacity else 0.0
        ),
        volunteer_capacity_utilization=(
            len(assigned) / volunteer_pickup_capacity
            if volunteer_pickup_capacity else 0.0
        ),
    )


def comparison_rows(fifo, greedy):
    return [
        ("Donations received",
         fifo.donations_received,
         greedy.donations_received),
        ("Donations assigned",
         fifo.donations_assigned,
         greedy.donations_assigned),
        ("Donations unassigned",
         fifo.donations_unassigned,
         greedy.donations_unassigned),
        ("Food quantity rescued",
         fifo.food_quantity_rescued,
         greedy.food_quantity_rescued),
        ("Food quantity at risk",
         fifo.food_quantity_at_risk,
         greedy.food_quantity_at_risk),
        ("Urgent rescue rate",
         fifo.urgent_rescue_rate,
         greedy.urgent_rescue_rate),
        ("Recipient capacity utilization",
         fifo.recipient_capacity_utilization,
         greedy.recipient_capacity_utilization),
        ("Volunteer capacity utilization",
         fifo.volunteer_capacity_utilization,
         greedy.volunteer_capacity_utilization),
    ]
