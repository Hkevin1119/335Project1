from fifo import schedule_fifo
from greedy import schedule_greedy
from loader import load_simulation_data
from metrics import calculate_metrics, comparison_rows


def print_percentage(value):
    return f"{value:.1%}"


def print_summary(fifo_metrics, greedy_metrics):
    percentage_metrics = {
        "Urgent rescue rate",
        "Recipient capacity utilization",
        "Volunteer capacity utilization",
    }

    print("--- Final Summary Table ---")
    print(f"{'Metric':<35} {'FIFO':>12} {'Greedy':>12}")
    print("-" * 61)

    for name, fifo_value, greedy_value in comparison_rows(
        fifo_metrics,
        greedy_metrics,
    ):
        if name in percentage_metrics:
            fifo_display = print_percentage(fifo_value)
            greedy_display = print_percentage(greedy_value)
        else:
            fifo_display = str(fifo_value)
            greedy_display = str(greedy_value)

        print(
            f"{name:<35} "
            f"{fifo_display:>12} "
            f"{greedy_display:>12}"
        )


def main():
    donations, recipients, volunteers = load_simulation_data(
        "scenario.json"
    )

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

    print_summary(fifo_metrics, greedy_metrics)


if __name__ == "__main__":
    main()
