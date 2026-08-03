import json
import logging
from app.schemas import SensorPacketCreate

logger = logging.getLogger("gateway.packet_parser")


class PacketParseError(Exception):
    pass


class PacketParser:
    """
    Packet Parser (Requirement 13):
    Pipeline: SX1278 bytes -> decode('utf-8') -> json.loads() -> Pydantic Validation.
    No binary parser.
    """

    @staticmethod
    def parse(raw_bytes: bytes) -> SensorPacketCreate:
        if not raw_bytes:
            raise PacketParseError("Received empty payload bytes.")

        try:
            raw_str = raw_bytes.decode("utf-8").strip()
            logger.debug(f"PacketParser: Decoding string: {raw_str}")
        except UnicodeDecodeError as exc:
            logger.warning(f"PacketParser: UTF-8 decode failed: {exc}")
            raise PacketParseError(f"UTF-8 decode failed: {exc}") from exc

        try:
            data = json.loads(raw_str)
        except json.JSONDecodeError as exc:
            logger.warning(f"PacketParser: Malformed JSON string: {exc}")
            raise PacketParseError(f"Malformed JSON packet: {exc}") from exc

        if not isinstance(data, dict):
            raise PacketParseError("JSON payload must be a key-value dictionary object.")

        try:
            packet = SensorPacketCreate(**data)
            logger.info(f"PacketParser: Parsed packet_id={packet.packet_id}, type={packet.packet_type}")
            return packet
        except Exception as exc:
            logger.warning(f"PacketParser: Pydantic validation error: {exc}")
            raise PacketParseError(f"Pydantic validation failed: {exc}") from exc
