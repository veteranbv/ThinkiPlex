"""
Utilities for parallel processing.

This module provides functions for running tasks in parallel.
"""

import concurrent.futures
from typing import Any, Callable, Iterable, List, TypeVar

from .logging import get_logger

logger = get_logger()

T = TypeVar('T')
R = TypeVar('R')


def parallel_map(
    func: Callable[[T], R],
    items: Iterable[T],
    max_workers: int = 4,
    timeout: int = None
) -> List[R]:
    """Execute a function on multiple items in parallel.
    
    Args:
        func: The function to execute
        items: The items to process
        max_workers: Maximum number of worker processes
        timeout: Timeout in seconds for each task
        
    Returns:
        List of results
    """
    results = []
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_item = {executor.submit(func, item): item for item in items}
        
        # Process results as they complete
        for future in concurrent.futures.as_completed(future_to_item, timeout=timeout):
            item = future_to_item[future]
            try:
                result = future.result()
                results.append(result)
                logger.debug(f"Successfully processed {item}")
            except Exception as e:
                logger.error(f"Error processing {item}: {e}")
                
    return results