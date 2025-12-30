"""
PDF-to-Markdown Extractor - Resource Usage Monitor (Feature #71).

Monitors and logs CPU and memory usage during extraction.
"""

import time
from typing import Dict, Any
import psutil

from loguru import logger


class ResourceMonitor:
    """
    Monitor resource usage during extraction (Feature #71).

    Tracks CPU and memory usage to help identify performance bottlenecks
    and prevent resource exhaustion.

    Example:
        >>> monitor = ResourceMonitor()
        >>> monitor.start()
        >>> # ... do extraction ...
        >>> stats = monitor.stop()
        >>> print(f"Peak memory: {stats['peak_memory_mb']} MB")
    """

    def __init__(self):
        """Initialize resource monitor."""
        self.process = psutil.Process()
        self.start_time = None
        self.start_memory = None
        self.start_cpu_percent = None
        self.peak_memory_mb = 0.0
        self.samples = []

    def start(self) -> None:
        """
        Start monitoring resources.

        Records baseline CPU and memory usage.

        Example:
            >>> monitor = ResourceMonitor()
            >>> monitor.start()
        """
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / (1024 ** 2)  # MB
        self.start_cpu_percent = self.process.cpu_percent()
        self.peak_memory_mb = self.start_memory
        self.samples = []

        logger.debug(
            f"Resource monitoring started: "
            f"memory={self.start_memory:.1f}MB, cpu={self.start_cpu_percent:.1f}%"
        )

    def sample(self) -> Dict[str, float]:
        """
        Take a resource usage sample.

        Returns:
            dict: Current resource usage.
                {
                    'timestamp': float,
                    'memory_mb': float,
                    'cpu_percent': float,
                }

        Example:
            >>> monitor = ResourceMonitor()
            >>> monitor.start()
            >>> sample = monitor.sample()
            >>> print(f"Current memory: {sample['memory_mb']} MB")
        """
        current_memory = self.process.memory_info().rss / (1024 ** 2)  # MB
        current_cpu = self.process.cpu_percent()

        # Update peak memory
        if current_memory > self.peak_memory_mb:
            self.peak_memory_mb = current_memory

        sample_data = {
            'timestamp': time.time(),
            'memory_mb': current_memory,
            'cpu_percent': current_cpu,
        }

        self.samples.append(sample_data)

        return sample_data

    def stop(self) -> Dict[str, Any]:
        """
        Stop monitoring and return statistics.

        Returns:
            dict: Resource usage statistics.
                {
                    'duration_seconds': float,
                    'start_memory_mb': float,
                    'end_memory_mb': float,
                    'peak_memory_mb': float,
                    'memory_delta_mb': float,
                    'avg_cpu_percent': float,
                    'sample_count': int,
                }

        Example:
            >>> monitor = ResourceMonitor()
            >>> monitor.start()
            >>> # ... extraction ...
            >>> stats = monitor.stop()
            >>> logger.info(f"Peak memory: {stats['peak_memory_mb']} MB")
        """
        if self.start_time is None:
            logger.warning("Monitor not started, returning empty stats")
            return {}

        duration = time.time() - self.start_time
        end_memory = self.process.memory_info().rss / (1024 ** 2)  # MB
        memory_delta = end_memory - self.start_memory

        # Calculate average CPU if samples exist
        if self.samples:
            avg_cpu = sum(s['cpu_percent'] for s in self.samples) / len(self.samples)
        else:
            avg_cpu = self.process.cpu_percent()

        stats = {
            'duration_seconds': duration,
            'start_memory_mb': self.start_memory,
            'end_memory_mb': end_memory,
            'peak_memory_mb': self.peak_memory_mb,
            'memory_delta_mb': memory_delta,
            'avg_cpu_percent': avg_cpu,
            'sample_count': len(self.samples),
        }

        logger.info(
            f"Resource monitoring stopped: "
            f"duration={duration:.2f}s, peak_memory={self.peak_memory_mb:.1f}MB, "
            f"memory_delta={memory_delta:+.1f}MB, avg_cpu={avg_cpu:.1f}%"
        )

        return stats

    def get_current_usage(self) -> Dict[str, float]:
        """
        Get current system resource usage.

        Returns:
            dict: System-wide resource usage.
                {
                    'system_memory_percent': float,
                    'system_memory_available_gb': float,
                    'system_cpu_percent': float,
                }

        Example:
            >>> monitor = ResourceMonitor()
            >>> usage = monitor.get_current_usage()
            >>> if usage['system_memory_percent'] > 90:
            ...     logger.warning("System memory critical!")
        """
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=0.1)

        return {
            'system_memory_percent': memory.percent,
            'system_memory_available_gb': memory.available / (1024 ** 3),
            'system_cpu_percent': cpu_percent,
        }
