from pathlib import Path


ML_ROOT = Path(__file__).resolve().parent
MODEL_PATH = ML_ROOT / "model" / "priority_model.pkl"
PREPROCESSOR_PATH = ML_ROOT / "preprocessing" / "preprocessor.pkl"

PACKET_TYPE_CODES = {"SOS": 1, "HAZARD": 2, "MESSAGE": 3}
PRIORITY_LABELS = {1: "LOW", 2: "MEDIUM", 3: "HIGH", 4: "CRITICAL"}
SUPPORTED_PACKET_TYPES = frozenset(PACKET_TYPE_CODES)
REQUIRED_FEATURES = (
	"packet_type",
	"heart_rate",
	"spo2",
	"battery",
	"retry_count",
	"hop_count",
)
