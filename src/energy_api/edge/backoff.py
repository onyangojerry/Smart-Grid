# Author: Jerry Onyango
# Contribution: Boots the FastAPI application, registers domain routers, and serves health and contract endpoints.
from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field


@dataclass
class BackoffConfig:
    base_delay: float = 0.5
    multiplier: float = 2.0
    max_delay: float = 30.0
    max_attempts: int = 8
    cooldown: float = 60.0


@dataclass
class BackoffState:
    config: BackoffConfig
    attempt_count: int = 0
    last_attempt_at: float = 0.0
    in_cooldown: bool = False
    cooldown_started_at: float = 0.0

    def __post_init__(self) -> None:
        self.config = BackoffConfig() if self.config is None else self.config


class Backoff:
    def __init__(self, config: BackoffConfig | None = None) -> None:
        self.state = BackoffState(config=config or BackoffConfig())

    @property
    def current_delay(self) -> float:
        if self.state.in_cooldown:
            elapsed = time.time() - self.state.cooldown_started_at
            remaining = self.state.config.cooldown - elapsed
            return max(0, remaining)
        delay = self.state.config.base_delay * (self.state.config.multiplier ** self.state.attempt_count)
        return min(delay, self.state.config.max_delay)

    def record_success(self) -> None:
        self.state.attempt_count = 0
        self.state.in_cooldown = False
        self.state.last_attempt_at = time.time()

    def record_failure(self) -> bool:
        self.state.attempt_count += 1
        self.state.last_attempt_at = time.time()

        if self.state.attempt_count >= self.state.config.max_attempts:
            self.state.in_cooldown = True
            self.state.cooldown_started_at = time.time()
            return False
        return True

    @property
    def should_retry(self) -> bool:
        if self.state.in_cooldown:
            elapsed = time.time() - self.state.cooldown_started_at
            if elapsed < self.state.config.cooldown:
                return False
            self.state.in_cooldown = False
            self.state.attempt_count = 0
        return True

    def add_jitter(self, delay: float, jitter_factor: float = 0.1) -> float:
        jitter = delay * jitter_factor * (2 * random.random() - 1)
        return max(0, delay + jitter)

    async def wait(self) -> None:
        if not self.state.last_attempt_at:
            return
        delay = self.add_jitter(self.current_delay)
        await asyncio.sleep(delay)

    def reset(self) -> None:
        self.state = BackoffState(config=self.state.config)


def backoff_with_retry(
    func,
    max_attempts: int | None = None,
    config: BackoffConfig | None = None,
) -> tuple[bool, Exception | None]:
    backoff = Backoff(config)
    if max_attempts:
        backoff.state.config = BackoffConfig(
            max_attempts=max_attempts,
            base_delay=config.base_delay if config else 0.5,
            multiplier=config.multiplier if config else 2.0,
            max_delay=config.max_delay if config else 30.0,
        )

    while True:
        if not backoff.should_retry:
            return False, None

        try:
            result = func()
            backoff.record_success()
            return True, None
        except Exception as e:
            if not backoff.record_failure():
                return False, e
            backoff.state.last_attempt_at = time.time()
            time.sleep(backoff.add_jitter(backoff.current_delay))
