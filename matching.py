from dataclasses import dataclass

from models import Assignment, Status

TRAVEL_MINUTES = 15  # simplifying assumption: fixed pickup->delivery time


def fmt(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


@dataclass
class State:
    capacity_left: dict
    volunteer_free_at: dict
    pickups_done: dict

    @classmethod
    def fresh(cls, recipients, volunteers):
        return cls(
            {r.recipient_id: r.capacity for r in recipients},
            {v.volunteer_id: v.available_from for v in volunteers},
            {v.volunteer_id: 0 for v in volunteers},
        )


def find_match(d, recipients, volunteers, state):
    """Return (recipient, volunteer, pickup_time, None) for the first feasible
    pair, or (None, None, None, reason) explaining why none exists."""
    if d.ready_time + TRAVEL_MINUTES > d.expiry_time:
        return None, None, None, (
            f"it cannot be delivered before it expires (ready {fmt(d.ready_time)}, "
            f"expires {fmt(d.expiry_time)}, delivery needs {TRAVEL_MINUTES} min)")

    type_ok = [r for r in recipients if d.food_type in r.accepted_types]
    if not type_ok:
        return None, None, None, f"no recipient accepts food type '{d.food_type}'"

    cap_ok = [r for r in type_ok if state.capacity_left[r.recipient_id] >= d.quantity]
    if not cap_ok:
        return None, None, None, (
            f"no compatible recipient had {d.quantity} units of remaining capacity")

    vols = [v for v in volunteers
            if v.area == d.pickup_area
            and v.vehicle_capacity >= d.quantity
            and state.pickups_done[v.volunteer_id] < v.max_pickups]
    if not vols:
        return None, None, None, (
            f"no volunteer in area '{d.pickup_area}' with vehicle capacity >= {d.quantity} "
            f"and pickups remaining")

    for r in cap_ok:
        for v in vols:
            pickup = max(d.ready_time, state.volunteer_free_at[v.volunteer_id])
            deliver = pickup + TRAVEL_MINUTES
            if (deliver <= d.expiry_time and deliver <= r.closing_time
                    and deliver <= v.available_until):
                return r, v, pickup, None

    return None, None, None, (
        "no recipient/volunteer pair could complete delivery before the donation "
        "expired, the recipient closed, or the volunteer's shift ended")


def commit(d, r, v, pickup, state):
    state.capacity_left[r.recipient_id] -= d.quantity
    state.volunteer_free_at[v.volunteer_id] = pickup + TRAVEL_MINUTES
    state.pickups_done[v.volunteer_id] += 1


def assigned(d, r, v, pickup, state_before_cap):
    reason = (
        f"Donation {d.donation_id} ({d.quantity} units of {d.food_type}) was assigned "
        f"to {r.organization_name} with volunteer {v.volunteer_id}, pickup at {fmt(pickup)}, because "
        f"it expires at {fmt(d.expiry_time)}, {r.organization_name} accepts {d.food_type} and had "
        f"{state_before_cap} units of capacity free, and the volunteer's vehicle "
        f"holds {v.vehicle_capacity}.")
    return Assignment(d.donation_id, r.recipient_id, v.volunteer_id, pickup,
                      Status.ASSIGNED, reason)


def unassigned(d, why):
    return Assignment(d.donation_id, None, None, None, Status.UNASSIGNED,
                      f"Donation {d.donation_id} could not be assigned because {why}.")


def run_in_order(ordered_donations, recipients, volunteers):
    """Process donations in the given order. Strategies = different orderings."""
    state = State.fresh(recipients, volunteers)
    history = []
    for d in ordered_donations:
        r, v, pickup, why = find_match(d, recipients, volunteers, state)
        if r is None:
            history.append(unassigned(d, why))
        else:
            before = state.capacity_left[r.recipient_id]
            commit(d, r, v, pickup, state)
            history.append(assigned(d, r, v, pickup, before))
    return history
