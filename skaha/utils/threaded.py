"""General purpose threaded scaler."""

import asyncio
import concurrent.futures
from functools import partial
from typing import Any, Callable, Dict, List


async def scale(
    function: Callable[..., Any],
    arguments: List[Dict[Any, Any]],
) -> List[Any]:
    """Scales a function across multiple arguments.

    Args:
        function (Callable[..., Any]): The function to be scaled.
        arguments (List[Dict[Any, Any]], optional): The arguments to be passed to each
            function, by default [{}]

    Returns:
        List: The results of the function.

    Examples:
        >>> from skaha.threaded import scale
            from asyncio import get_event_loop
            loop = get_event_loop()
            loop.run_until_complete(
                scale(lambda x: x**2, [{'x': i} for i in range(10)])
            )
    """
    workers = len(arguments)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(executor, partial(function, **arguments[index]))
            for index in range(workers)
        ]
        return await asyncio.gather(*futures, return_exceptions=True)


def get_event_loop() -> asyncio.AbstractEventLoop:
    """Get the event loop.

    Returns:
        asyncio.AbstractEventLoop: The event loop.

    Examples:
        >>> from skaha.threaded import get_event_loop
            loop = get_event_loop()
    """
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop
