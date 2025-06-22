import argparse
import csv
import sys
from tabulate import tabulate
from typing import List, Dict, Union, Optional
from pathlib import Path


def parse_where_condition(condition: str) -> tuple[str, str, Union[str, float]]:
    operators = [">", "<", "="]
    for op in operators:
        if op in condition:
            parts = condition.split(op)
            if len(parts) == 2:
                column = parts[0]
                value = parts[1]
                try:
                    value = float(value) if "." in value else int(value)
                except ValueError:
                    pass
                return column, op, value
    raise ValueError(f"Invalid condition format: {condition}")


def parse_aggregate(aggregate: str) -> tuple[str, str]:
    if "=" not in aggregate:
        raise ValueError(f"Invalid aggregate format: {aggregate}")
    column, func = aggregate.split("=")
    if func not in ["avg", "min", "max"]:
        raise ValueError(f"Unsupported aggregate function: {func}")
    return column, func


def filter_data(
        data: List[Dict[str, Union[str, float]]], condition: Optional[str]
) -> List[Dict[str, Union[str, float]]]:
    if not condition:
        return data

    column, op, value = parse_where_condition(condition)

    filtered = []
    for row in data:
        row_value = row[column]
        try:
            row_value = float(row_value) if isinstance(row_value, str) and "." in row_value else int(row_value)
        except (ValueError, TypeError):
            pass

        if op == ">" and row_value > value:
            filtered.append(row)
        elif op == "<" and row_value < value:
            filtered.append(row)
        elif op == "=":
            if isinstance(value, str) and str(row_value) == value:
                filtered.append(row)
            elif not isinstance(value, str) and row_value == value:
                filtered.append(row)
    return filtered


def aggregate_data(
        data: List[Dict[str, Union[str, float]]], aggregate: Optional[str]
) -> List[Dict[str, float]]:
    if not aggregate:
        return []

    column, func = parse_aggregate(aggregate)

    values = []
    for row in data:
        try:
            value = float(row[column])
            values.append(value)
        except (ValueError, TypeError):
            raise ValueError(f"Cannot aggregate non-numeric column: {column}")

    if not values:
        return []

    result = {}
    if func == "avg":
        result["avg"] = sum(values) / len(values)
    elif func == "min":
        result["min"] = min(values)
    elif func == "max":
        result["max"] = max(values)

    return [result]


def read_csv(file_path: str) -> List[Dict[str, Union[str, float]]]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, mode="r") as file:
        reader = csv.DictReader(file)
        return [
            {k.strip(): v.strip() if isinstance(v, str) else v
             for k, v in row.items()}
            for row in reader
        ]

def main():
    parser = argparse.ArgumentParser(description="Process CSV file with filtering and aggregation.")
    parser.add_argument("--file", required=True, help="Path to CSV file")
    parser.add_argument("--where", help="Filter condition, e.g. 'rating>4.7'")
    parser.add_argument("--aggregate", help="Aggregate function, e.g. 'rating=avg'")

    args = parser.parse_args()

    try:
        data = read_csv(args.file)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        filtered_data = filter_data(data, args.where)
    except ValueError as e:
        print(f"Error in filter condition: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        if args.aggregate:
            result = aggregate_data(filtered_data if args.where else data, args.aggregate)
            if result:
                print(tabulate(result, headers="keys", tablefmt="simple"))
            else:
                print("No data to aggregate")
        else:
            display_data = filtered_data if args.where else data
            if display_data:
                print(tabulate(display_data, headers="keys", tablefmt="simple"))
            else:
                print("No data matches the filter condition")
    except ValueError as e:
        print(f"Error in aggregation: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()