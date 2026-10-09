"""Strategy B: greedy urgency-first.

GREEDY RULE (state this exactly in the README):
  1. Schedule donations with the LEAST remaining shelf life first
     (remaining_shelf_life = expiry_time - ready_time, in minutes).
  2. If tied, schedule the LARGER quantity first.
  3. If still tied, schedule the donation that ARRIVED earlier.

Local choice: at each step the most time-critical donation gets first claim on
recipient capacity and volunteer time. Feasibility and recipient/volunteer choice
are identical to FIFO (matching.find_match), so only the ORDER differs.
"""
from dataclasses import replace

from matching import run_in_order


def priority_key(d):
    return (d.remaining_shelf_life, -d.quantity, d.arrival_order)


def _why_ahead(jumper, d):
    if jumper.remaining_shelf_life < d.remaining_shelf_life:
        return (f"{jumper.donation_id} had less remaining shelf life "
                f"({jumper.remaining_shelf_life} min vs {d.remaining_shelf_life} min)")
    return (f"{jumper.donation_id} had equal remaining shelf life but a larger "
            f"quantity ({jumper.quantity} vs {d.quantity})")


def _ordering_note(d, earlier_in_greedy):
    """Explain why d was considered after donations that arrived later than it."""
    jumpers = [j for j in earlier_in_greedy if j.arrival_order > d.arrival_order]
    if not jumpers:
        return ""
    shown = jumpers[:3]
    more = f" (and {len(jumpers) - 3} more)" if len(jumpers) > 3 else ""
    reasons = "; ".join(_why_ahead(j, d) for j in shown)
    return (f" Under the urgency-first rule it was considered after "
            f"{', '.join(j.donation_id for j in shown)}{more} although it arrived "
            f"earlier: {reasons}.")


def schedule_greedy(donations, recipients, volunteers):
    ordered = sorted(donations, key=priority_key)           # O(D log D)
    history = run_in_order(ordered, recipients, volunteers)
    # Explanation pass only: O(D^2) worst case; does not affect any decision.
    result = []
    for i, (d, a) in enumerate(zip(ordered, history)):
        note = _ordering_note(d, ordered[:i])
        result.append(replace(a, decision_reason=a.decision_reason + note) if note else a)
    return result
