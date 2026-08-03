import logging
from pydantic import BaseModel
from app.schemas import SensorPacketCreate

logger = logging.getLogger("gateway.packet_validator")


class ValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = []


class PacketValidator:
    """
    Validates packet attributes before database processing.
    Rejects malformed or invalid packets.
    """

    @staticmethod
    def validate(packet: SensorPacketCreate) -> ValidationResult:
        errors = []

        if not packet.packet_id or len(packet.packet_id.strip()) == 0:
            errors.append("packet_id cannot be empty.")

        target_node = packet.source_node_id or packet.node_id
        if not target_node or len(target_node.strip()) == 0:
            errors.append("source_node_id / node_id cannot be empty.")

        if packet.battery < 0 or packet.battery > 100:
            errors.append(f"Invalid battery level: {packet.battery}% (must be 0-100).")

        if packet.latitude is not None:
            if packet.latitude < -90 or packet.latitude > 90:
                errors.append(f"Invalid latitude: {packet.latitude}")

        if packet.longitude is not None:
            if packet.longitude < -180 or packet.longitude > 180:
                errors.append(f"Invalid longitude: {packet.longitude}")

        if errors:
            logger.warning(f"Packet validation failed for {packet.packet_id}: {errors}")
            return ValidationResult(is_valid=False, errors=errors)

        return ValidationResult(is_valid=True, errors=[])
