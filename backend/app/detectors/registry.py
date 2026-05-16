from app.detectors.base import Detector, StaticFinding
from app.detectors.reentrancy import ReentrancyDetector
from app.detectors.access_control import AccessControlDetector
from app.detectors.integer_overflow import IntegerOverflowDetector
from app.detectors.unchecked_calls import UncheckedCallsDetector
from app.detectors.oracle_manipulation import OracleManipulationDetector
from app.detectors.signature_replay import SignatureReplayDetector
from app.detectors.flash_loan import FlashLoanDetector
from app.detectors.delegatecall import DelegatecallDetector

DETECTORS: list[Detector] = [
    ReentrancyDetector(),
    AccessControlDetector(),
    IntegerOverflowDetector(),
    UncheckedCallsDetector(),
    OracleManipulationDetector(),
    SignatureReplayDetector(),
    FlashLoanDetector(),
    DelegatecallDetector(),
]


def run_all_detectors(source: str, filename: str = "") -> list[StaticFinding]:
    findings: list[StaticFinding] = []
    for detector in DETECTORS:
        try:
            findings.extend(detector.detect(source, filename))
        except Exception as e:
            # Never let one detector crash the whole scan
            print(f"[detector] {detector.__class__.__name__} error on {filename}: {e}")
    return findings
