import pytest
import csv
from pathlib import Path
from main import (
    parse_where_condition,
    parse_aggregate,
    filter_data,
    aggregate_data,
    read_csv,
)


@pytest.fixture
def sample_data():
    return [
        {"name": "iphone 15 pro", "brand": "apple", "price": "999", "rating": "4.9"},
        {"name": "galaxy s23 ultra", "brand": "samsung", "price": "1199", "rating": "4.8"},
        {"name": "redmi note 12", "brand": "xiaomi", "price": "199", "rating": "4.6"},
    ]



@pytest.fixture
def temp_csv(tmp_path, sample_data):
    csv_file = tmp_path / "test.csv"
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "brand", "price", "rating"])
        writer.writeheader()
        writer.writerows(sample_data)
    return csv_file



def test_parse_where_condition():
    assert parse_where_condition("rating>4.5") == ("rating", ">", 4.5)
    assert parse_where_condition("price<1000") == ("price", "<", 1000)
    assert parse_where_condition("brand=apple") == ("brand", "=", "apple")

    with pytest.raises(ValueError):
        parse_where_condition("invalid_condition")



def test_parse_aggregate():
    assert parse_aggregate("rating=avg") == ("rating", "avg")
    assert parse_aggregate("price=max") == ("price", "max")

    with pytest.raises(ValueError):
        parse_aggregate("invalid_aggregate")

    with pytest.raises(ValueError):
        parse_aggregate("rating=unknown")



def test_filter_data(sample_data):
    # Фильтр по числовому значению
    filtered = filter_data(sample_data, "rating>4.7")
    assert len(filtered) == 2
    assert filtered[0]["name"] == "iphone 15 pro"
    assert filtered[1]["name"] == "galaxy s23 ultra"

    filtered = filter_data(sample_data, "brand=apple")
    assert len(filtered) == 1
    assert filtered[0]["name"] == "iphone 15 pro"

    assert filter_data(sample_data, None) == sample_data

    with pytest.raises(ValueError):
        filter_data(sample_data, "invalid_filter")


def test_aggregate_data(sample_data):
    result = aggregate_data(sample_data, "rating=avg")
    assert len(result) == 1
    assert pytest.approx(result[0]["avg"]) == (4.9 + 4.8 + 4.6) / 3

    result = aggregate_data(sample_data, "price=max")
    assert len(result) == 1
    assert result[0]["max"] == 1199

    result = aggregate_data(sample_data, "rating=min")
    assert len(result) == 1
    assert result[0]["min"] == 4.6

    with pytest.raises(ValueError):
        aggregate_data(sample_data, "brand=avg")


def test_read_csv(temp_csv, sample_data):
    data = read_csv(str(temp_csv))
    assert len(data) == 3
    assert data == sample_data

    with pytest.raises(FileNotFoundError):
        read_csv("nonexistent.csv")


def test_integration(temp_csv):
    from main import main  # замените 'your_module' на имя вашего модуля
    import sys
    from io import StringIO

    original_stdout = sys.stdout
    original_stderr = sys.stderr

    try:
        sys.argv = ["script.py", "--file", str(temp_csv), "--where", "rating>4.7"]
        sys.stdout = StringIO()
        main()
        output = sys.stdout.getvalue()
        assert "iphone 15 pro" in output
        assert "galaxy s23 ultra" in output
        assert "redmi note 12" not in output

        sys.argv = ["script.py", "--file", str(temp_csv), "--aggregate", "rating=avg"]
        sys.stdout = StringIO()
        main()
        output = sys.stdout.getvalue()
        assert "avg" in output

        sys.argv = ["script.py", "--file", str(temp_csv), "--where", "brand=apple", "--aggregate", "price=avg"]
        sys.stdout = StringIO()
        main()
        output = sys.stdout.getvalue()
        assert "avg" in output
        assert "999" in output  # только iphone 15 pro подходит под фильтр

    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr