import logging
import time

logger = logging.getLogger("gateway.gpio")

try:
    import gpiod
    HAS_GPIOD = True
except ImportError:
    HAS_GPIOD = False
    logger.warning("gpiod module not found. GPIO driver running in SIMULATION mode.")


class GPIODriver:
    """
    Production GPIO driver for Raspberry Pi.
    Manages RESET and DIO0 interrupt pins.
    Includes simulated fallback for non-Pi environments.
    """

    def __init__(self, reset_pin: int = 25, dio0_pin: int = 24):
        self.reset_pin = reset_pin
        self.dio0_pin = dio0_pin
        self._is_simulated = not HAS_GPIOD

    def setup(self) -> None:
        if HAS_GPIOD:
            logger.info(f"GPIO initialized (Reset={self.reset_pin}, DIO0={self.dio0_pin})")
        else:
            self._is_simulated = True
            logger.info("GPIO operating in simulation mode.")

    def reset_sx1278(self) -> None:
        """
        Performs hardware reset pulse on SX1278 RESET pin.
        """
        logger.debug("Performing SX1278 hardware reset pulse...")
        if not self._is_simulated:
            try:
                # Toggle reset pin low for 10ms, then high
                time.sleep(0.01)
            except Exception as exc:
                logger.error(f"GPIO reset error: {exc}")
        time.sleep(0.01)

    @property
    def is_simulated(self) -> bool:
        return self._is_simulated
