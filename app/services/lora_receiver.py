import asyncio
import logging

from app.core.database import SessionLocal
from app.drivers.lora_manager import lora_manager
from app.services.packet_parser import PacketParseError, PacketParser
from app.services.packet_processor import PacketProcessor

logger = logging.getLogger("gateway.lora_receiver")


class LoRaReceiver:
    """
    LoRa Receiver Background Task (Requirement 5 & 21):
    Continuously listens for incoming LoRa packets over SPI via LoRaManager.
    Flow: SX1278 -> LoRaManager -> PacketParser -> PacketProcessor.
    No serial implementation.
    """

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if not self._running:
            self._running = True
            # Initialize LoRa hardware via LoRaManager
            await lora_manager.initialize()
            self._task = asyncio.create_task(self._receiver_loop())
            logger.info("SPI LoRa Receiver task started.")

    async def stop(self) -> None:
        if self._running:
            self._running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
            logger.info("SPI LoRa Receiver task stopped.")

    async def _receiver_loop(self) -> None:
        logger.info("Entering continuous LoRa RX loop...")

        while self._running:
            try:
                # Requirement 5: Receive packet strictly via LoRaManager
                raw_bytes, rssi, snr = await lora_manager.receive_packet(timeout_sec=0.5)

                if not raw_bytes:
                    await asyncio.sleep(0.05)
                    continue

                logger.info(f"LoRa Receiver: Received {len(raw_bytes)} bytes packet. RSSI: {rssi}dBm, SNR: {snr}dB")

                # Step 1: Requirement 13 — Parse JSON bytes
                try:
                    packet = PacketParser.parse(raw_bytes)
                except PacketParseError as exc:
                    logger.warning(f"LoRa Receiver: Dropping unparseable packet: {exc}")
                    continue

                # Step 2: Process packet through pipeline
                db = SessionLocal()
                try:
                    res = await PacketProcessor.process_packet(
                        db=db, packet=packet, rssi=rssi, snr=snr
                    )
                    logger.info(f"LoRa Receiver Result: {res.message}")
                except Exception as exc:
                    logger.exception(f"LoRa Receiver DB Error: {exc}")
                finally:
                    db.close()

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.exception(f"Unexpected error in LoRa Receiver loop: {exc}")
                await asyncio.sleep(1.0)


lora_receiver = LoRaReceiver()