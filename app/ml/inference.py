import logging
from typing import Any, Mapping

from app.ml.predictor import PriorityPredictionError, predict_priority
from app.schemas import PacketType, SensorPacketCreate

logger = logging.getLogger("gateway.ml.inference")


def resolve_packet_type(packet: SensorPacketCreate) -> SensorPacketCreate:
	"""Resolve predefined MESSAGE values before they reach the ML model."""
	if packet.packet_type != PacketType.MESSAGE:
		return packet
	message = (packet.message or "").strip().upper()
	if message == PacketType.SOS.value:
		return packet.model_copy(update={"packet_type": PacketType.SOS, "sos": True})
	if message == PacketType.HAZARD.value:
		return packet.model_copy(update={"packet_type": PacketType.HAZARD})
	return packet


def infer_priority(packet: SensorPacketCreate | Mapping[str, Any]) -> dict[str, int | str]:
	if isinstance(packet, SensorPacketCreate):
		if packet.packet_type == PacketType.HEARTBEAT:
			raise PriorityPredictionError("HEARTBEAT packets are excluded from priority inference")
		packet = resolve_packet_type(packet)
		packet = packet.model_dump()
	try:
		return predict_priority(packet)
	except PriorityPredictionError:
		logger.exception("Priority inference failed")
		raise
