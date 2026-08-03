import asyncio
import logging
from typing import Any

from app.drivers.lora_manager import lora_manager

logger = logging.getLogger("gateway.ack_queue")


class ACKQueue:
    """
    ACK Queue (Requirement 7):
    Buffers generated ACK packets and asynchronously transmits them via LoRaManager.
    Flow: ACK Generation -> ACK Queue -> LoRaManager -> SX1278.
    """

    def __init__(self):
        self.queue: asyncio.Queue[bytes] = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._running = False
        self.total_enqueued = 0
        self.total_transmitted = 0
        self.total_failed = 0

    async def enqueue(self, ack_bytes: bytes) -> None:
        await self.queue.put(ack_bytes)
        self.total_enqueued += 1
        logger.info(f"ACK Queue: Enqueued ACK packet ({len(ack_bytes)} bytes). Queue size: {self.queue.qsize()}")

    async def start(self) -> None:
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._worker_loop())
            logger.info("ACK Queue worker task started.")

    async def stop(self) -> None:
        if self._running:
            self._running = False
            if self._worker_task:
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass
            logger.info("ACK Queue worker task stopped.")

    async def _worker_loop(self) -> None:
        while self._running:
            try:
                ack_bytes = await self.queue.get()
                logger.info(f"ACK Queue Worker: Processing ACK transmission ({len(ack_bytes)} bytes)...")

                # Transmit through LoRaManager (Requirement 5 & 7)
                success = await lora_manager.transmit_ack(ack_bytes)
                if success:
                    self.total_transmitted += 1
                    logger.info("ACK Queue Worker: ACK successfully transmitted over LoRa.")
                else:
                    self.total_failed += 1
                    logger.error("ACK Queue Worker: ACK transmission failed.")

                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.exception(f"ACK Queue Worker Error: {exc}")
                await asyncio.sleep(0.5)


ack_queue = ACKQueue()
