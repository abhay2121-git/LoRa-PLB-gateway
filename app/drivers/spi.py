import logging

logger = logging.getLogger("gateway.spi")

try:
    import spidev
    HAS_SPIDEV = True
except ImportError:
    HAS_SPIDEV = False
    logger.warning("spidev module not found. SPI driver running in SIMULATION mode.")


class SPIDriver:
    """
    Production SPI driver wrapping Linux spidev.
    Provides transfer, read_register, and write_register operations.
    Includes simulated fallback for non-Linux / development environments.
    """

    def __init__(self, bus: int = 0, device: int = 0, speed_hz: int = 5000000):
        self.bus = bus
        self.device = device
        self.speed_hz = speed_hz
        self.spi = None
        self._is_simulated = not HAS_SPIDEV

    def open(self) -> None:
        if HAS_SPIDEV:
            try:
                self.spi = spidev.SpiDev()
                self.spi.open(self.bus, self.device)
                self.spi.max_speed_hz = self.speed_hz
                self.spi.mode = 0
                logger.info(f"SPI initialized on bus {self.bus}, device {self.device}")
            except Exception as exc:
                logger.error(f"Failed to open SPI bus: {exc}. Falling back to simulation.")
                self._is_simulated = True
        else:
            self._is_simulated = True
            logger.info("SPI operating in simulation mode.")

    def close(self) -> None:
        if self.spi and HAS_SPIDEV:
            try:
                self.spi.close()
            except Exception:
                pass
        self.spi = None

    def transfer(self, data: list[int] | bytes) -> list[int]:
        if self._is_simulated or not self.spi:
            # Simulated dummy response
            return [0] * len(data)
        return self.spi.xfer2(list(data))

    def write_register(self, address: int, value: int) -> None:
        # High bit set for SPI write on SX1278
        reg = (address | 0x80) & 0xFF
        self.transfer([reg, value & 0xFF])

    def read_register(self, address: int) -> int:
        # High bit cleared for SPI read on SX1278
        reg = address & 0x7F
        resp = self.transfer([reg, 0x00])
        return resp[1] if len(resp) > 1 else 0

    @property
    def is_simulated(self) -> bool:
        return self._is_simulated
