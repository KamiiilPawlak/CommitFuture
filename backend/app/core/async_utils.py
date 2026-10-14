import asyncio
from collections.abc import Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any


def run_coroutine_sync(coroutine: Coroutine[Any, Any, None]) -> None:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(coroutine)
        return

    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(asyncio.run, coroutine).result()
