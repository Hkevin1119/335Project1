from dataclasses import dataclass
from enum import Enum


class Status(str, Enum):
    """Decision outcomes named in the brief's explainability table (Section 5)."""
    ASSIGNED = "ASSIGNED"
    UNASSIGNED = "UNASSIGNED"
    DEFERRED = "DEFERRED"   # reserved for the greedy strategy's ordering explanations


@dataclass(frozen=True)
class Donation:
    donation_id: str
    donor_name: str
    food_type: str
    quantity: int
    expiry_time: int      # absolute deadline: must be delivered by this minute
    pickup_area: str
    ready_time: int       # earliest pickup minute
    arrival_order: int    # position in the input (FIFO key / final tie-breaker)

    @property
    def remaining_shelf_life(self) -> int:
        """Minutes of shelf life left when the food is ready for pickup.
        Brief lists 'expiry/remaining shelf life' as one field; we store the
        absolute expiry and derive this, so the greedy rule can use either."""
        return self.expiry_time - self.ready_time


@dataclass(frozen=True)
class Recipient:
    recipient_id: str
    organization_name: str
    accepted_types: frozenset   # set of accepted food types
    capacity: int
    area: str
    closing_time: int


@dataclass(frozen=True)
class Volunteer:
    volunteer_id: str
    vehicle_capacity: int
    area: str
    available_from: int       # availability window start
    available_until: int      # availability window end
    max_pickups: int


@dataclass(frozen=True)
class Assignment:
    donation_id: str
    recipient_id: str | None      # None when UNASSIGNED
    volunteer_id: str | None      # None when UNASSIGNED
    scheduled_time: int | None    # pickup minute; None when UNASSIGNED
    status: Status
    decision_reason: str
