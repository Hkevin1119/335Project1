# Food Donation Scheduling Simulator

This project compares two scheduling strategies over the **same donation, recipient, and volunteer input data**:

- **FIFO baseline:** processes donations by arrival order.
- **Greedy urgency-first:** prioritizes donations with the least remaining shelf life.

Both strategies use the same feasibility and matching logic. Only the order in which donations are considered changes.

## Architecture

The project is divided into small modules with separate responsibilities:

| Module | Responsibility |
|---|---|
| `models.py` | Immutable domain models and assignment statuses |
| `loader.py` | Loads the master JSON scenario and constructs model objects |
| `matching.py` | Shared feasibility checks, matching, state updates, and explanations |
| `fifo.py` | FIFO ordering strategy |
| `greedy.py` | Greedy urgency-first ordering and ordering explanations |
| `metrics.py` | Calculates performance metrics for a completed simulation |
| Main script | Loads one scenario, runs both strategies, and prints results and the final comparison table |
| `tests/` | Automated tests for scheduling, metrics, normal cases, and edge cases |

The execution flow is:

```text
scenario.JSON
    -> loader.load_simulation_data
    -> donations, recipients, volunteers
    -> schedule_fifo -------------------> run_in_order
    -> schedule_greedy -> priority sort -> run_in_order
    -> calculate_metrics for each strategy
    -> FIFO-versus-greedy comparison
```

`matching.run_in_order` creates a fresh simulation state for every run. FIFO and greedy therefore receive the same input objects but do not share consumed capacity, volunteer availability, or pickup counts.

### Shared matching process

For each donation, `matching.find_match`:

1. Rejects a donation that cannot be delivered before expiry.
2. Finds recipients that accept its food type.
3. Filters recipients by remaining capacity.
4. Finds volunteers in the pickup area with enough vehicle capacity and pickup allowance.
5. Selects the first recipient-volunteer pair that can deliver before:
   - the donation expires,
   - the recipient closes, and
   - the volunteer's shift ends.
6. Commits the assignment by reducing recipient capacity and updating volunteer state.

Recipient and volunteer list order determines which feasible pair is selected first. The strategies change donation order only; they do not change this matching behavior.

## Data Model

Time values are integer minutes. For example, `600` represents 10:00 and `720` represents 12:00.

### Donation

| Field | Meaning |
|---|---|
| `donation_id` | Unique donation identifier |
| `donor_name` | Donor name |
| `food_type` | Type of donated food |
| `quantity` | Number of food units |
| `expiry_time` | Absolute delivery deadline in minutes |
| `pickup_area` | Area in which a volunteer must collect the donation |
| `ready_time` | Earliest pickup time in minutes |
| `arrival_order` | FIFO key and final greedy tie-breaker |
| `remaining_shelf_life` | Derived as `expiry_time - ready_time` |

### Recipient

| Field | Meaning |
|---|---|
| `recipient_id` | Unique recipient identifier |
| `organization_name` | Display name |
| `accepted_types` | Immutable set of accepted food types |
| `capacity` | Maximum food quantity available for assignment |
| `area` | Recipient area; currently stored but not used in travel calculations |
| `closing_time` | Latest permitted delivery time |

### Volunteer

| Field | Meaning |
|---|---|
| `volunteer_id` | Unique volunteer identifier |
| `vehicle_capacity` | Maximum quantity carried in one pickup |
| `area` | Pickup area served by the volunteer |
| `available_from` | Start of availability window |
| `available_until` | End of availability window |
| `max_pickups` | Maximum number of assignments during the simulation |

### Assignment

| Field | Meaning |
|---|---|
| `donation_id` | Donation being reported |
| `recipient_id` | Selected recipient, or `None` when unassigned |
| `volunteer_id` | Selected volunteer, or `None` when unassigned |
| `scheduled_time` | Pickup time, or `None` when unassigned |
| `status` | `ASSIGNED`, `UNASSIGNED`, or reserved `DEFERRED` |
| `decision_reason` | Human-readable explanation of the outcome |

## Scheduling Strategies

### FIFO baseline

FIFO sorts donations by ascending `arrival_order` and passes that ordering to the shared matching engine. Python's sort is stable, so duplicate arrival values retain their original input order.

```python
ordered = sorted(donations, key=lambda d: d.arrival_order)
```

FIFO favors arrival fairness, but an early, less urgent donation may consume resources needed by a later donation with a shorter shelf life.

### Greedy urgency-first

The README requirement is stated precisely below:

```text
GREEDY RULE:
  1. Schedule donations with the LEAST remaining shelf life first
     (remaining_shelf_life = expiry_time - ready_time, in minutes).
  2. If tied, schedule the LARGER quantity first.
  3. If still tied, schedule the donation that ARRIVED earlier.
```

This rule is implemented by:

```python
def priority_key(d):
    return (d.remaining_shelf_life, -d.quantity, d.arrival_order)
```

The greedy choice is local: the currently highest-priority donation gets first claim on recipient capacity and volunteer time. It does not search all possible schedules or guarantee a globally optimal result.

## Metrics and Comparison

Both strategies must be evaluated using the same loaded lists of donations, recipients, and volunteers.

| Metric | Definition |
|---|---|
| Donations received | Total number of input donations |
| Donations assigned | Number of assignments with status `ASSIGNED` |
| Donations unassigned | Number of assignments with status `UNASSIGNED` |
| Food quantity rescued | Sum of quantities for assigned donations |
| Food quantity at risk | Sum of quantities for unassigned donations |
| Urgent rescue rate | Urgent donations assigned divided by urgent donations received |
| Recipient capacity utilization | Rescued quantity divided by total recipient capacity |
| Volunteer capacity utilization | Completed pickups divided by total volunteer pickup allowance |
| FIFO-versus-greedy comparison | Differences in ordering, assignments, pickup times, quantities, and utilization |

For reporting, this project defines an **urgent donation** as one with no more than 120 minutes of remaining shelf life:

```text
remaining_shelf_life <= 120
```

Zero-denominator metrics return `0.0`.

### Final summary table for the supplied scenario

| Metric | FIFO | Greedy urgency-first | Change |
|---|---:|---:|---:|
| Donations received | 8 | 8 | 0 |
| Donations assigned | 4 | 4 | 0 |
| Donations unassigned | 4 | 4 | 0 |
| Food quantity rescued | 100 units | 100 units | 0 |
| Food quantity at risk | 175 units | 175 units | 0 |
| Urgent rescue rate | 75.0% | 75.0% | 0.0 percentage points |
| Recipient capacity utilization | 41.7% | 41.7% | 0.0 percentage points |
| Volunteer capacity utilization | 30.8% | 30.8% | 0.0 percentage points |

Greedy changes the order and pickup times but not the final assigned set in the supplied scenario. In particular, urgent donation `D-4` is considered ahead of `D-1` and `D-3`, giving it earlier access to the Downtown volunteer. All three still fit within the available capacity and time windows, so aggregate outcomes remain equal.

The unassigned outcomes are unaffected by strategy:

- `D-EXPIRED` cannot complete the fixed 15-minute delivery before expiry.
- `D-BAD-TYPE` has a food type accepted by no recipient.
- `D-OVER-CAP` exceeds every compatible recipient's remaining capacity.
- `D-NO-VOL` has no qualifying volunteer in its pickup area.

## Complexity Analysis

Let:

- `D` be the number of donations,
- `R` be the number of recipients, and
- `V` be the number of volunteers.

### FIFO

Sorting donations costs:

```text
O(D log D)
```

For each donation, matching may scan recipients, volunteers, and all candidate recipient-volunteer pairs. Its worst-case cost is:

```text
O(D * R * V)
```

Overall FIFO time complexity is:

```text
O(D log D + D * R * V)
```

Simulation state and assignment history require:

```text
O(R + V + D) space
```

### Greedy urgency-first

Priority sorting also costs:

```text
O(D log D)
```

It uses the same matching engine, so scheduling costs:

```text
O(D * R * V)
```

The ordering-explanation pass compares each donation with previously considered donations and is quadratic in the worst case:

```text
O(D^2)
```

Overall greedy time complexity is therefore:

```text
O(D log D + D * R * V + D^2)
```

Space complexity is:

```text
O(R + V + D)
```

The quadratic explanation pass affects reporting only and does not change scheduling decisions.

## Automated Tests

The automated test suite should cover:

- A normal successful assignment.
- Unsupported food types.
- Insufficient recipient capacity.
- Insufficient volunteer vehicle capacity.
- Donations that expire before delivery can finish.
- Recipient closing times and volunteer shift limits.
- Volunteer pickup limits and sequential availability.
- Empty donation, recipient, and volunteer lists.
- FIFO first-arrival behavior under constrained capacity.
- Every greedy tie-breaker.
- A case in which FIFO and greedy assign different donations.
- Greedy ordering explanations.
- A finite-batch starvation case.
- Metric calculations, urgent rescue rate, zero denominators, and food at risk.
- Confirmation that both strategies use the same input data but fresh simulation state.

Run all tests from the project root with:

```bash
python -m unittest discover -s tests -v
```

## Limitations

- **Fixed travel time:** Every pickup-to-delivery trip takes exactly 15 minutes, regardless of distance or traffic.
- **No travel to pickup:** Volunteer travel to a donor and travel after delivery are not modeled.
- **No route optimization:** Each donation is matched independently; multi-stop routes are not considered.
- **No donation splitting:** A donation must fit entirely within one recipient's remaining capacity and one volunteer's vehicle.
- **First feasible match:** Recipient and volunteer selection follows input order rather than optimizing distance, utilization, fairness, or total rescued quantity.
- **Static batch:** Donations are sorted once. New donations do not arrive while the simulation is running.
- **Local greedy behavior:** Urgency-first can starve earlier, less urgent donations and does not guarantee the optimal global schedule.
- **Fixed urgency threshold:** The 120-minute threshold is a reporting definition, not part of matching feasibility or greedy priority.
- **Simplified capacity metrics:** Recipient utilization treats food units as directly comparable across food types. Volunteer utilization uses pickup slots, not distance, hours, or vehicle load percentage.
- **No partial or deferred scheduling:** Failed donations are marked unassigned; `DEFERRED` is reserved but not currently produced.
- **Input order affects ties:** Equal FIFO keys or complete greedy ties retain JSON list order because Python sorting is stable.
- **Input validation is limited:** Malformed records, negative quantities, invalid time ranges, and duplicate identifiers should be rejected explicitly.
- **Duplicate data in the supplied scenario:** `R1` and `V1` each appear twice, and arrival-order values are duplicated. State dictionaries key resources by ID, while raw utilization denominators count JSON rows. This makes the supplied utilization percentages potentially misleading until duplicate records are removed or rejected.
- **Case-sensitive filename risk:** The supplied file is named `scenario.JSON`, while code that opens `scenario.json` may fail on case-sensitive systems.

## Recommended Data Validation

Before simulation, validate that:

- Donation, recipient, and volunteer IDs are unique.
- `arrival_order` values are unique when strict FIFO ordering is required.
- Quantities, capacities, vehicle capacities, and pickup limits are non-negative.
- `ready_time <= expiry_time`.
- `available_from <= available_until`.
- Required top-level JSON sections and record fields are present.
- The scenario filename uses consistent casing across environments.
