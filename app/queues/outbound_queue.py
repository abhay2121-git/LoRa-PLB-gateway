import asyncio
import json
import logging
from typing import Any

from app.core.database import SessionLocal
from app.crud import update_outbound_status
from app.drivers.lora_manager import lora_manager

logger = logging.getLogger("gateway.outbound_queue")


class OutboundJob:
    def __init__(self, message_id: str, payload_bytes: bytes):
        self.message_id = message_id
        self.payload_bytes = payload_bytes


class OutboundQueue:
    """
    Outbound Queue (Requirement 8):
    Buffers outgoing gateway messages (Delivery Confirmations, Status Messages, Hazards, Config Updates)
    and transmits them asynchronously via LoRaManager.
    Flow: Dashboard/Service -> Outbound Queue -> LoRaManager -> SX1278.
    """

    def __init__(self):
        self.queue: asyncio.Queue[OutboundJob] = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._running = False
        self.total_enqueued = 0
        self.total_transmitted = 0
        self.total_failed = 0

    async def enqueue(self, message_id: str, payload_bytes: bytes) -> None:
        job = OutboundJob(message_id=message_id, payload_bytes=payload_bytes)
        await self.queue.put(job)
        self.total_enqueued += 1
        logger.info(
            f"Outbound Queue: Enqueued message {message_id} ({len(payload_bytes)} bytes). "
            f"Queue size: {self.queue.qsize()}"
        )

    async def start(self) -> None:
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._worker_loop())
            logger.info("Outbound Queue worker task started.")

    async def stop(self) -> None:
        if self._running:
            self._running = False
            if self._worker_task:
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass
            logger.info("Outbound Queue worker task stopped.")

    async def _worker_loop(self) -> None:
        while self._running:
            try:
                job = await self.queue.get()
                logger.info(f"Outbound Queue Worker: Transmitting message {job.message_id}...")

                # Transmit through LoRaManager (Requirement 5 & 8)
                success = await lora_manager.transmit_outbound_message(job.payload_bytes)

                db = SessionLocal()
                try:
                    if success:
                        self.total_transmitted += 1
                        update_outbound_status(db, message_id=job.message_id, status="SENT", sent=True)
                        logger.info(f"Outbound Queue Worker: Message {job.message_id} SENT successfully.")
                    else:
                        self.total_failed += 1
                        update_outbound_status(db, message_id=job.message_id, status="FAILED", sent=False)
                        logger.error(f"Outbound Queue Worker: Message {job.message_id} FAILED transmission.")
                finally:
                    db.close()

                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.exception(f"Outbound Queue Worker Error: {exc}")
                await asyncio.sleep(0.5)


outbound_queue = OutboundQueue()
