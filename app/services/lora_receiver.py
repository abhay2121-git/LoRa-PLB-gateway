"""
LoRa Receiver Service

Continuously listens for LoRa packets from the ESP32 over
the Raspberry Pi serial interface and forwards valid packets
to the packet handler.
"""

import json
import logging
import time

import serial
from serial import SerialException

from app.core.config import settings
from app.core.database import SessionLocal
from app.schemas import SensorPacketCreate
from app.services.packet_handler import process_packet


logger = logging.getLogger(__name__)


class LoRaReceiver:
    def __init__(self):
        """
        Serial connection is initialized later so the
        gateway can start even if the LoRa module is
        temporarily unavailable.
        """
        self.serial_connection = None

    def connect(self) -> None:
        """
        Continuously attempts to connect to the LoRa module.
        """

        while True:

            try:

                logger.info(
                    f"Connecting to {settings.serial_port}..."
                )

                self.serial_connection = serial.Serial(
                    port=settings.serial_port,
                    baudrate=settings.serial_baudrate,
                    timeout=1,
                )

                logger.info(
                    "LoRa module connected successfully."
                )

                return

            except SerialException as exc:

                logger.warning(
                    f"Unable to connect: {exc}"
                )

                logger.info(
                    "Retrying in 5 seconds..."
                )

                time.sleep(5)

    def start(self) -> None:
        """
        Starts listening for LoRa packets forever.
        """

        logger.info("LoRa Receiver Started.")

        self.connect()

        while True:

            try:

                if self.serial_connection is None:
                    self.connect()

                if self.serial_connection.in_waiting == 0:
                    time.sleep(0.05)
                    continue

                raw_packet = (
                    self.serial_connection.readline()
                    .decode("utf-8")
                    .strip()
                )

                if not raw_packet:
                    continue

                logger.info(
                    f"Packet Received: {raw_packet}"
                )

                packet_dict = json.loads(raw_packet)

                packet = SensorPacketCreate(
                    **packet_dict
                )

                db = SessionLocal()

                try:

                    result = process_packet(
                        db=db,
                        packet=packet,
                    )

                    db.commit()

                    logger.info(result.message)

                except Exception as exc:

                    db.rollback()

                    logger.exception(
                        f"Database Error: {exc}"
                    )

                finally:

                    db.close()

            except json.JSONDecodeError:

                logger.warning(
                    "Received malformed JSON packet."
                )

            except SerialException as exc:

                logger.error(
                    f"Serial connection lost: {exc}"
                )

                try:
                    self.serial_connection.close()
                except Exception:
                    pass

                self.serial_connection = None

                self.connect()

            except Exception as exc:

                logger.exception(
                    f"Unexpected Error: {exc}"
                )

                time.sleep(1)