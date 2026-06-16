"""Fila serial para exportações Excel COM (EXCEL.EXE não é thread-safe)."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, TypeVar

T = TypeVar("T")

_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="excel-export")
_lock = asyncio.Lock()


async def run_excel_export_job(func: Callable[..., T], *args, **kwargs) -> T:
    """Executa job de export COM em thread única, serializando requests simultâneos."""
    loop = asyncio.get_running_loop()
    async with _lock:
        return await loop.run_in_executor(_executor, lambda: func(*args, **kwargs))
