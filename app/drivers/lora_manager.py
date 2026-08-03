import asyncio
import logging
from typing import Any

from app.core.config import settings
from app.drivers.gpio import GPIODriver
from app.drivers.spi import SPIDriver
from app.drivers.sx1278 import SX1278Driver

logger = logging.getLogger("gateway.lora_manager")


class LoRaManager:
    """
    LoRaManager (Requirement 5):
    Sole gateway between high-level Services and the physical SX1278 Hardware Driver.
    Services MUST NEVER access SPI or the SX1278 driver directly.

    Responsibilities:
    - Receive Packet
    - Transmit Packet
    - Transmit ACK
    - Transmit Delivery Confirmation
    - Transmit Status Message
    - Manage Radio Access (Thread-safe via asyncio.Lock)
    """

    def __init__(self):
        self.spi_driver = SPIDriver(bus=settings.spi_bus, device=settings.spi_device)
        self.gpio_driver = GPIODriver(
            reset_pin=settings.gpio_reset_pin, dio0_pin=settings.gpio_dio0_pin
        )
        self.sx1278_driver = SX1278Driver(spi=self.spi_driver, gpio=self.gpio_driver)
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        async with self._lock:
            if not self._initialized:
                logger.info("Initializing LoRaManager hardware drivers...")
                self.gpio_driver.setup()
                self.sx1278_driver.initialize(
                    frequency_mhz=settings.lora_frequency,
                    bandwidth_hz=settings.lora_bandwidth,
                    spreading_factor=settings.lora_spreading_factor,
                    coding_rate=settings.lora_coding_rate,
                    tx_power_dbm=settings.lora_tx_power,
                )
                self._initialized = True
                logger.info("LoRaManager initialized successfully.")

    async def receive_packet(
        self, timeout_sec: float = 1.0
    ) -> tuple[bytes | None, int, float]:
        """
        Polls radio for incoming bytes.
        """
        async with self._lock:
            return self.sx1278_driver.receive_packet(timeout_sec=timeout_sec)

    async def transmit_packet(self, payload: bytes) -> bool:
        """
        Transmits raw bytes over SX1278.
        """
        async with self._lock:
            logger.info(f"LoRaManager: Transmitting {len(payload)} bytes payload...")
            success = self.sx1278_driver.transmit_packet(payload)
            if success:
                logger.info("LoRaManager: Packet transmission successful.")
            else:
                logger.error("LoRaManager: Packet transmission failed.")
            return success

    async def transmit_ack(self, ack_payload: bytes) -> bool:
        """
        Transmits an ACK packet.
        """
        logger.info("LoRaManager: Transmitting ACK packet...")
        return await self.transmit_packet(ack_payload)

    async def transmit_delivery_confirmation(self, confirmation_payload: bytes) -> bool:
        """
        Transmits a Delivery Confirmation packet.
        """
        logger.info("LoRaManager: Transmitting Delivery Confirmation packet...")
        return await self.transmit_packet(confirmation_payload)

    async def transmit_status_message(self, status_payload: bytes) -> bool:
        """
        Transmits a Status Message packet.
        """
        logger.info("LoRaManager: Transmitting Status Message packet...")
        return await self.transmit_packet(status_payload)

    def get_radio_status(self) -> dict[str, Any]:
        return {
            "frequency_mhz": settings.lora_frequency,
            "bandwidth_hz": settings.lora_bandwidth,
            "spreading_factor": settings.lora_spreading_factor,
            "tx_power_dbm": settings.lora_tx_power,
            "rssi": self.sx1278_driver.read_rssi(),
            "snr": self.sx1278_driver.read_snr(),
            "is_simulated": self.spi_driver.is_simulated,
        }

    async def shutdown(self) -> None:
        async with self._lock:
            self.spi_driver.close()
            self._initialized = False
            logger.info("LoRaManager shutdown complete.")


# Global singleton instance of LoRaManager
lora_manager = LoRaManager()
