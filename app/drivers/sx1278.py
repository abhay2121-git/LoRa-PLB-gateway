import logging
import time
from app.drivers.spi import SPIDriver
from app.drivers.gpio import GPIODriver

logger = logging.getLogger("gateway.sx1278")

# SX1278 Registers
REG_FIFO = 0x00
REG_OP_MODE = 0x01
REG_FRF_MSB = 0x06
REG_FRF_MID = 0x07
REG_FRF_LSB = 0x08
REG_PA_CONFIG = 0x09
REG_FIFO_ADDR_PTR = 0x0D
REG_FIFO_TX_BASE_ADDR = 0x0E
REG_FIFO_RX_BASE_ADDR = 0x0F
REG_FIFO_RX_CURRENT_ADDR = 0x10
REG_IRQ_FLAGS = 0x12
REG_RX_NB_BYTES = 0x13
REG_PKT_SNR_VALUE = 0x19
REG_PKT_RSSI_VALUE = 0x1A
REG_MODEM_CONFIG_1 = 0x1D
REG_MODEM_CONFIG_2 = 0x1E
REG_MODEM_CONFIG_3 = 0x26
REG_DIO_MAPPING_1 = 0x40
REG_DIO_MAPPING_2 = 0x41
REG_VERSION = 0x42

# Modes
MODE_LONG_RANGE_MODE = 0x80
MODE_SLEEP = 0x00
MODE_STDBY = 0x01
MODE_TX = 0x03
MODE_RX_CONTINUOUS = 0x05
MODE_RX_SINGLE = 0x06

# IRQ Flags
IRQ_RX_DONE_MASK = 0x40
IRQ_PAYLOAD_CRC_ERROR_MASK = 0x20
IRQ_TX_DONE_MASK = 0x08


class SX1278Driver:
    """
    Low-level SX1278 LoRa Transceiver Hardware Driver.
    SPI & GPIO access only. Contains NO business logic (Requirement 6).
    Enables hardware CRC via register RegModemConfig2 (Requirement 14).
    """

    def __init__(self, spi: SPIDriver, gpio: GPIODriver):
        self.spi = spi
        self.gpio = gpio
        self._current_rssi = -100
        self._current_snr = 0.0

    def initialize(
        self,
        frequency_mhz: float = 433.0,
        bandwidth_hz: int = 125000,
        spreading_factor: int = 7,
        coding_rate: int = 5,
        tx_power_dbm: int = 17,
    ) -> bool:
        """
        Initializes SX1278 transceiver in LoRa mode with hardware CRC enabled.
        """
        self.spi.open()
        self.gpio.reset_sx1278()

        if self.spi.is_simulated:
            logger.info("SX1278 initialized in SIMULATION mode.")
            return True

        # Check version register
        version = self.spi.read_register(REG_VERSION)
        if version != 0x12:
            logger.warning(f"SX1278 chip version mismatch. Expected 0x12, got {hex(version)}.")

        # Put module in sleep mode to allow setting LoRa mode
        self.set_mode(MODE_SLEEP)
        time.sleep(0.01)

        # Set LoRa mode (LongRangeMode bit 7 = 1)
        self.spi.write_register(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_SLEEP)
        time.sleep(0.01)

        # Set Standby mode
        self.set_mode(MODE_STDBY)

        # Set Frequency
        self.set_frequency(frequency_mhz)

        # Set Modem Config 1 (BW & CR)
        # BW: 125kHz = 0x70, CR 4/5 = 0x02
        bw_val = 0x70  # default 125kHz
        cr_val = ((coding_rate - 4) & 0x07) << 1
        self.spi.write_register(REG_MODEM_CONFIG_1, bw_val | cr_val)

        # Set Modem Config 2 (SF & Hardware CRC enable bit 2)
        # Requirement 14: Enable SX1278 hardware CRC
        sf_val = (spreading_factor & 0x0F) << 4
        crc_on_val = 0x04  # bit 2 = RxPayloadCrcOn
        self.spi.write_register(REG_MODEM_CONFIG_2, sf_val | crc_on_val)

        # Set Modem Config 3 (AGC auto on = 0x04)
        self.spi.write_register(REG_MODEM_CONFIG_3, 0x04)

        # Set PA Config (TX Power)
        self.set_tx_power(tx_power_dbm)

        # Set FIFO base addresses
        self.spi.write_register(REG_FIFO_TX_BASE_ADDR, 0x00)
        self.spi.write_register(REG_FIFO_RX_BASE_ADDR, 0x00)

        # Set to RX Continuous mode
        self.set_mode(MODE_RX_CONTINUOUS)

        logger.info(
            f"SX1278 configured: Freq={frequency_mhz}MHz, SF={spreading_factor}, "
            f"BW={bandwidth_hz}Hz, Hardware CRC=Enabled"
        )
        return True

    def set_mode(self, mode: int) -> None:
        if self.spi.is_simulated:
            return
        self.spi.write_register(REG_OP_MODE, MODE_LONG_RANGE_MODE | (mode & 0x07))

    def set_frequency(self, frequency_mhz: float) -> None:
        if self.spi.is_simulated:
            return
        frf = int((frequency_mhz * 1000000.0) / 61.03515625)
        self.spi.write_register(REG_FRF_MSB, (frf >> 16) & 0xFF)
        self.spi.write_register(REG_FRF_MID, (frf >> 8) & 0xFF)
        self.spi.write_register(REG_FRF_LSB, frf & 0xFF)

    def set_tx_power(self, power_dbm: int) -> None:
        if self.spi.is_simulated:
            return
        # PA_BOOST pin output for high power (17dBm)
        self.spi.write_register(REG_PA_CONFIG, 0x80 | (power_dbm - 2))

    def read_rssi(self) -> int:
        if self.spi.is_simulated:
            return self._current_rssi
        raw_rssi = self.spi.read_register(REG_PKT_RSSI_VALUE)
        self._current_rssi = -157 + raw_rssi
        return self._current_rssi

    def read_snr(self) -> float:
        if self.spi.is_simulated:
            return self._current_snr
        raw_snr = self.spi.read_register(REG_PKT_SNR_VALUE)
        # 2's complement conversion
        if raw_snr & 0x80:
            snr = ((raw_snr ^ 0xFF) + 1) * -0.25
        else:
            snr = raw_snr * 0.25
        self._current_snr = snr
        return self._current_snr

    def receive_packet(self, timeout_sec: float = 1.0) -> tuple[bytes | None, int, float]:
        """
        Polls SX1278 for received LoRa packet.
        Returns (payload_bytes, rssi, snr) or (None, 0, 0.0) if no packet received.
        Hardware CRC automatically discards corrupted packets if RegModemConfig2 CRC is set.
        """
        if self.spi.is_simulated:
            return None, -100, 0.0

        irq_flags = self.spi.read_register(REG_IRQ_FLAGS)

        # Check RxDone flag
        if not (irq_flags & IRQ_RX_DONE_MASK):
            return None, 0, 0.0

        # Check CRC error flag (Requirement 14: Hardware CRC)
        if irq_flags & IRQ_PAYLOAD_CRC_ERROR_MASK:
            logger.warning("SX1278 hardware CRC error detected in received packet. Dropping.")
            # Clear IRQ flags
            self.spi.write_register(REG_IRQ_FLAGS, 0xFF)
            return None, 0, 0.0

        # Read packet length and address
        bytes_nb = self.spi.read_register(REG_RX_NB_BYTES)
        current_addr = self.spi.read_register(REG_FIFO_RX_CURRENT_ADDR)

        # Set FIFO pointer to current packet start
        self.spi.write_register(REG_FIFO_ADDR_PTR, current_addr)

        # Read payload bytes from FIFO
        payload = bytearray()
        for _ in range(bytes_nb):
            payload.append(self.spi.read_register(REG_FIFO))

        # Clear IRQ flags
        self.spi.write_register(REG_IRQ_FLAGS, 0xFF)

        rssi = self.read_rssi()
        snr = self.read_snr()

        return bytes(payload), rssi, snr

    def transmit_packet(self, payload: bytes) -> bool:
        """
        Transmits raw bytes over SX1278 LoRa.
        """
        if self.spi.is_simulated:
            logger.info(f"[SIMULATED TX] Transmitted {len(payload)} bytes over SX1278.")
            return True

        self.set_mode(MODE_STDBY)

        # Reset FIFO pointer
        self.spi.write_register(REG_FIFO_ADDR_PTR, 0x00)
        self.spi.write_register(REG_FIFO_TX_BASE_ADDR, 0x00)

        # Write payload bytes to FIFO
        for byte in payload:
            self.spi.write_register(REG_FIFO, byte)

        # Set payload length
        self.spi.write_register(0x22, len(payload))

        # Put in TX mode
        self.set_mode(MODE_TX)

        # Wait for TxDone
        start_time = time.time()
        while time.time() - start_time < 3.0:
            flags = self.spi.read_register(REG_IRQ_FLAGS)
            if flags & IRQ_TX_DONE_MASK:
                # Clear IRQ flags
                self.spi.write_register(REG_IRQ_FLAGS, 0xFF)
                # Return to RX mode
                self.set_mode(MODE_RX_CONTINUOUS)
                return True
            time.sleep(0.01)

        logger.error("SX1278 TX timeout.")
        self.set_mode(MODE_RX_CONTINUOUS)
        return False
