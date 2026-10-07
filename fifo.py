from matching import run_in_order


def schedule_fifo(donations, recipients, volunteers):
    ordered = sorted(donations, key=lambda d: d.arrival_order)  
    return run_in_order(ordered, recipients, volunteers)
