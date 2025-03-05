from skaha.utils.convert import dict_to_tuples


def test_dict_to_tuples_empty():
    assert dict_to_tuples({}) == []


def test_dict_to_tuples_simple():
    assert dict_to_tuples({"a": 1, "b": 2}) == [("a", 1), ("b", 2)]


def test_dict_to_tuples_nested():
    assert dict_to_tuples({"a": {"x": 1, "y": 2}, "b": 3}) == [
        ("a", "x=1"),
        ("a", "y=2"),
        ("b", 3),
    ]


def test_dict_to_tuples_mixed():
    assert dict_to_tuples({"a": 1, "b": {"x": 2}, "c": {"y": 3, "z": 4}}) == [
        ("a", 1),
        ("b", "x=2"),
        ("c", "y=3"),
        ("c", "z=4"),
    ]


def test_dict_to_tuples_non_string_keys():
    assert dict_to_tuples({1: "a", 2: {"x": "b"}}) == [(1, "a"), (2, "x=b")]
