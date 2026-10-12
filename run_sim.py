from loader import load_simulation_data
from fifo import schedule_fifo
from greedy import schedule_greedy

# Loads data from JSON file
donations, recipients, volunteers = load_simulation_data("scenario.json")

print(f"Successfully loaded: {len(donations)} donation(s), {len(recipients)} recipient(s), and {len(volunteers)} volunteer(s).\n")

# Run FIFO Strategy
print("--- FIFO Simulation Results ---")
fifo_results = schedule_fifo(donations, recipients, volunteers)
for assignment in fifo_results:
    print(f"[{assignment.status}] Donation {assignment.donation_id}")
    print(f"  -> {assignment.decision_reason}\n")

# Run Greedy Strategy
print("--- Greedy Simulation Results ---")
greedy_results = schedule_greedy(donations, recipients, volunteers)
for assignment in greedy_results:
    print(f"[{assignment.status}] Donation {assignment.donation_id}")
    print(f"  -> {assignment.decision_reason}\n")