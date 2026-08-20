import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app import crud
from app.ml.inference import infer_priority, resolve_packet_type
from app.schemas import PacketProcessingResult, PacketType, SensorPacketCreate
from app.services.ack_service import AckService
from app.services.delivery_confirmation_service import DeliveryConfirmationService
from app.services.duplicate_detector import duplicate_detector
from app.services.emergency_detector import detect_emergency
from app.services.packet_validator import PacketValidator
from app.services.websocket_manager import manager as ws_manager

logger = logging.getLogger("gateway.packet_processor")


class PacketProcessor:
    """
    Main Packet Processing Pipeline Orchestrator.
    Flow:
    SX1278 -> PacketParser -> PacketValidator -> DuplicateDetector -> EmergencyDetector -> NodeManager -> DB -> Dashboard -> DeliveryConfirmation -> ACK
    """

    @staticmethod
    async def process_packet(
        db: Session,
        packet: SensorPacketCreate,
        rssi: int | None = None,
        snr: float | None = None,
    ) -> PacketProcessingResult:
        node_id = packet.source_node_id or packet.node_id or "UNKNOWN_NODE"

        try:
            # Step 1: Packet Validation
            val_res = PacketValidator.validate(packet)
            if not val_res.is_valid:
                logger.warning(f"Rejected malformed packet {packet.packet_id}: {val_res.errors}")
                return PacketProcessingResult(
                    success=False,
                    duplicate=False,
                    packet_id=packet.packet_id,
                    node_id=node_id,
                    packet_type=packet.packet_type,
                    message=f"Validation failed: {', '.join(val_res.errors)}",
                )

            # Step 2: Duplicate Check (Requirement 12)
            is_dup = await duplicate_detector.is_duplicate(db=db, packet_id=packet.packet_id)
            if is_dup:
                logger.warning(
                    f"[DUPLICATE] Packet {packet.packet_id} already processed. Generating ACK without duplicate DB entry."
                )
                # Requirement 12: Still generate ACK, do not store duplicate emergency
                await AckService.generate_and_enqueue_ack(
                    packet_id=packet.packet_id,
                    node_id=node_id,
                    packet_type=packet.packet_type,
                )
                return PacketProcessingResult(
                    success=True,
                    duplicate=True,
                    packet_id=packet.packet_id,
                    node_id=node_id,
                    packet_type=packet.packet_type,
                    emergency_id=packet.emergency_id,
                    sequence_number=packet.sequence_number,
                    emergency_detected=packet.packet_type != PacketType.HEARTBEAT,
                    ack_status=True,
                    message="Duplicate packet detected and ignored. ACK generated.",
                )

            # Register packet_id in duplicate detector memory set
            await duplicate_detector.register(packet.packet_id)

            # Resolve predefined MESSAGE values before emergency handling.
            packet = resolve_packet_type(packet)

            # Step 3: Category 1 — HEARTBEAT PACKETS (Requirement 10)
            if packet.packet_type == PacketType.HEARTBEAT:
                crud.update_node_heartbeat(db=db, packet=packet, rssi=rssi, snr=snr)
                db.commit()
                logger.info(f"[HEARTBEAT] Processed for Node {node_id}. Battery: {packet.battery}%")

                # Requirement 7: Generate and enqueue ACK
                await AckService.generate_and_enqueue_ack(
                    packet_id=packet.packet_id,
                    node_id=node_id,
                    packet_type=packet.packet_type,
                )

                # Broadcast to dashboard WebSocket
                await ws_manager.broadcast("HEARTBEAT_UPDATE", {"node_id": node_id, "battery": packet.battery})

                return PacketProcessingResult(
                    success=True,
                    duplicate=False,
                    packet_id=packet.packet_id,
                    node_id=node_id,
                    packet_type=packet.packet_type,
                    emergency_detected=False,
                    ack_status=True,
                    message=f"Heartbeat received for Node {node_id}. Status updated to ONLINE.",
                )

            # Step 4: Category 2 — EMERGENCY PACKETS (SOS, HAZARD, MESSAGE) (Requirement 11)
            emergency = detect_emergency(packet)
            priority_code = None
            priority = None
            priority_error = None
            try:
                priority_result = infer_priority(packet)
                priority_code = priority_result["priority_code"]
                priority = priority_result["priority"]
            except Exception as exc:
                priority_error = str(exc)
                logger.error("Priority engine unavailable for packet %s: %s", packet.packet_id, exc)

            # Emergency DB Pipeline: Node -> SensorLog -> PacketLog -> EmergencyEvent (Requirement 11)
            crud.create_or_update_node_emergency(db=db, packet=packet, rssi=rssi, snr=snr)
            crud.create_sensor_log(db=db, packet=packet)
            crud.create_or_update_emergency_event(
                db=db,
                packet=packet,
                event_type=emergency.event_type or packet.packet_type.value,
                remarks=emergency.remarks,
                priority_code=priority_code,
                priority_label=priority,
            )
            packet_log = crud.create_packet_log(db=db, packet=packet, rssi=rssi, snr=snr)

            db.commit()

            logger.info(
                f"[EMERGENCY] {packet.packet_type.value} stored for Node {node_id}. PacketID: {packet.packet_id}"
            )

            # Step 5: Generate Delivery Confirmation (Requirement 17 & 3)
            await DeliveryConfirmationService.process_and_send_delivery_confirmation(
                db=db, packet=packet
            )
            db.commit()

            # Step 6: Generate ACK (Requirement 7)
            await AckService.generate_and_enqueue_ack(
                packet_id=packet.packet_id,
                node_id=node_id,
                packet_type=packet.packet_type,
            )

            # Step 7: Broadcast Emergency Update to Dashboard WebSocket
            await ws_manager.broadcast(
                "EMERGENCY_ALERT",
                {
                    "packet_id": packet.packet_id,
                    "node_id": node_id,
                    "event_type": packet.packet_type.value,
                    "emergency_id": packet.emergency_id,
                    "latitude": packet.latitude,
                    "longitude": packet.longitude,
                    "priority_code": priority_code,
                    "priority": priority,
                },
            )

            return PacketProcessingResult(
                success=True,
                duplicate=False,
                packet_id=packet.packet_id,
                node_id=node_id,
                packet_type=packet.packet_type,
                emergency_id=packet.emergency_id,
                sequence_number=packet.sequence_number,
                emergency_detected=True,
                emergency_type=emergency.event_type,
                ack_status=packet_log.ack_status,
                delivery_confirmation_sent=True,
                priority_code=priority_code,
                priority=priority,
                priority_error=priority_error,
                message=f"Emergency packet {packet.packet_type.value} processed & stored successfully.",
            )

        except SQLAlchemyError as exc:
            db.rollback()
            logger.error(f"Database error processing packet {packet.packet_id}: {exc}")
            return PacketProcessingResult(
                success=False,
                duplicate=False,
                packet_id=packet.packet_id,
                node_id=node_id,
                packet_type=packet.packet_type,
                message=f"Database processing error: {exc}",
            )
        except Exception as exc:
            db.rollback()
            logger.exception(f"Unexpected error processing packet {packet.packet_id}: {exc}")
            return PacketProcessingResult(
                success=False,
                duplicate=False,
                packet_id=packet.packet_id,
                node_id=node_id,
                packet_type=packet.packet_type,
                message=f"Packet processing failed: {exc}",
            )


# Alias for backward compatibility
process_packet = PacketProcessor.process_packet
