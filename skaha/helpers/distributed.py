"""Helper functions for distributed computing."""

import os
from collections.abc import Iterable, Iterator
from typing import TypeVar

T = TypeVar("T")


def stripe(
    iterable: Iterable[T],
    replica: int = int(os.environ.get("REPLICA_ID", "1")),
    total: int = int(os.environ.get("REPLICA_COUNT", "1")),
) -> Iterator[T]:
    """Returns every `total`-th item from the iterable with a `replica`-th offset.

    Args:
        iterable (Iterable[T]): The iterable to partition.
        replica (int, optional): The replica number.
            Defaults to int(os.environ.get("REPLICA_ID", 1)).
        total (int, optional): The total number of replicas.
            Defaults to int(os.environ.get("REPLICA_COUNT", 1)).

    Examples:
        >>> from skaha.helpers import distributed
        >>> dataset = range(100)
        >>> for data in distributed.partition(dataset, 1, 10):
                print(data)
        0, 10, 20, 30, 40, 50, 60, 70, 80, 90

    Yields:
        Iterator[T]: The `replica`-th partition of the iterable.
    """
    offset = replica - 1
    for index, item in enumerate(iterable):
        if index % total == offset:
            yield item


def chunk(
    iterable: Iterable[T],
    replica: int = int(os.environ.get("REPLICA_ID", "1")),
    total: int = int(os.environ.get("REPLICA_COUNT", "1")),
) -> Iterator[T]:
    """Returns the `replica`-th chunk of the iterable split into `total` chunks.

    Args:
        iterable (Iterable[T]): The iterable to chunk.
        replica (int, optional): The replica number.
            Defaults to int(os.environ.get("REPLICA_ID", 1)).
        total (int, optional): The total number of replicas.
            Defaults to int(os.environ.get("REPLICA_COUNT", 1)).

    Examples:
        >>> from skaha.helpers import distributed
        >>> dataset = range(100)
        >>> for data in distributed.chunk(dataset, 1, 10):
                print(data)
        0,1,2,3,4,5,6,7,8,9

    Yields:
        Iterator[T]: The `replica`-th block of the iterable.
    """
    items = list(iterable)
    count = len(items)
    # integer chunk size (floor)
    size = count // total
    # start/end of this chunk
    start = replica * size
    # last replica picks up any remainder
    end = (replica + 1) * size if replica < total - 1 else count
    yield from items[start:end]
