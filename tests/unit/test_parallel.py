"""
Tests for the parallel processing utilities.
"""

import time
from concurrent.futures import TimeoutError

import pytest

from thinkiplex.utils.parallel import parallel_map


def test_parallel_map_success():
    """Test parallel_map with successful processing."""
    # Function that simulates work and returns input * 2
    def work_func(x):
        time.sleep(0.1)  # Simulate work
        return x * 2
    
    items = [1, 2, 3, 4, 5]
    results = parallel_map(work_func, items, max_workers=2)
    
    assert len(results) == len(items)
    assert results == [2, 4, 6, 8, 10]


def test_parallel_map_with_errors():
    """Test parallel_map with some failing tasks."""
    # Function that fails for even numbers
    def work_func(x):
        if x % 2 == 0:
            raise ValueError(f"Error for {x}")
        return x * 2
    
    items = [1, 2, 3, 4, 5]
    
    # Should not raise an exception, but some results will be missing
    results = parallel_map(work_func, items, max_workers=2)
    
    # Only odd numbers should have been processed successfully
    assert 2 not in results
    assert 8 not in results
    assert 2 in results
    assert 6 in results
    assert 10 in results


def test_parallel_map_timeout():
    """Test parallel_map with timeout."""
    # Function that takes longer than the timeout
    def slow_func(x):
        time.sleep(1.0)
        return x
    
    items = [1, 2, 3]
    
    # Should complete successfully but with no results due to timeout
    with pytest.raises(TimeoutError):
        parallel_map(slow_func, items, max_workers=2, timeout=0.5)