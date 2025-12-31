"""
PDF-to-Markdown Extractor - Webhook Utilities (Features #107-108).

Webhook callback implementation with retry logic.
"""

import time
from typing import Any, Dict, Optional
import httpx

from loguru import logger


class WebhookSender:
    """
    Webhook sender with retry logic (Features #107-108).

    Sends POST requests to callback URLs when jobs complete or fail.

    Example:
        >>> sender = WebhookSender()
        >>> sender.send(
        ...     callback_url="https://example.com/webhook",
        ...     payload={"job_id": "123", "status": "completed"}
        ... )
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: int = 5,
        backoff_multiplier: float = 2.0,
        timeout: int = 30,
    ):
        """
        Initialize webhook sender.

        Args:
            max_retries: Maximum retry attempts (Feature #108).
            retry_delay: Initial delay between retries in seconds.
            backoff_multiplier: Exponential backoff multiplier (Feature #108).
            timeout: Request timeout in seconds.
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_multiplier = backoff_multiplier
        self.timeout = timeout

    def send(
        self,
        callback_url: str,
        payload: Dict[str, Any],
    ) -> bool:
        """
        Send webhook with retry logic (Features #107-108).

        Args:
            callback_url: URL to send POST request to.
            payload: JSON payload to send.

        Returns:
            bool: True if webhook sent successfully.

        Example:
            >>> sender = WebhookSender()
            >>> success = sender.send(
            ...     "https://example.com/callback",
            ...     {"job_id": "123", "status": "completed"}
            ... )
        """
        logger.info(f"Sending webhook to {callback_url}")

        attempt = 0
        delay = self.retry_delay

        while attempt < self.max_retries:
            attempt += 1

            try:
                # Send POST request
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        callback_url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )

                    response.raise_for_status()

                    logger.info(
                        f"Webhook sent successfully: {callback_url} "
                        f"(status={response.status_code}, attempt={attempt})"
                    )

                    return True

            except httpx.HTTPError as e:
                logger.warning(
                    f"Webhook attempt {attempt}/{self.max_retries} failed: {e}"
                )

                # Feature #108: Retry with exponential backoff
                if attempt < self.max_retries:
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= self.backoff_multiplier
                else:
                    logger.error(
                        f"Webhook failed after {self.max_retries} attempts: {callback_url}"
                    )
                    return False

        return False

    async def send_async(
        self,
        callback_url: str,
        payload: Dict[str, Any],
    ) -> bool:
        """
        Send webhook asynchronously with retry logic.

        Args:
            callback_url: URL to send POST request to.
            payload: JSON payload to send.

        Returns:
            bool: True if webhook sent successfully.
        """
        logger.info(f"Sending async webhook to {callback_url}")

        attempt = 0
        delay = self.retry_delay

        while attempt < self.max_retries:
            attempt += 1

            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        callback_url,
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )

                    response.raise_for_status()

                    logger.info(
                        f"Async webhook sent: {callback_url} "
                        f"(status={response.status_code}, attempt={attempt})"
                    )

                    return True

            except httpx.HTTPError as e:
                logger.warning(
                    f"Async webhook attempt {attempt}/{self.max_retries} failed: {e}"
                )

                if attempt < self.max_retries:
                    logger.info(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    delay *= self.backoff_multiplier
                else:
                    logger.error(
                        f"Async webhook failed after {self.max_retries} attempts"
                    )
                    return False

        return False
