from typing import List


def get_average_of_field_entries(latency_records: List, field: str):
    return sum([getattr(latency_data, field) for latency_data in latency_records]) / len(latency_records)
