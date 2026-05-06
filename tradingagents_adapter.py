import json
import random
import threading
import time
import dataclasses
from pathlib import Path
from kronos_adapter import KronosAdapter


class MacroAgentAdapter:
    """Sprint A: slow-lane macro decision adapter (mock-first)."""

    def __init__(self, update_interval_sec: int = 3600, out_file: str = "macro_filter.json"):
        self.update_interval_sec = update_interval_sec
        self.out_file = Path(out_file)
        self._decision = {"bias": "NEUTRAL", "confidence": 0.5, "max_risk_multiplier": 1.0, "source": "INIT"}
        self._stop = threading.Event()
        self._thread = None
        self.kronos = KronosAdapter(out_file=out_file)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def get_decision(self):
        return self._decision.copy()

    def _worker(self):
        while not self._stop.is_set():
            try:
                decision_obj = self.kronos.run_once()
                self._decision = dataclasses.asdict(decision_obj)
            except Exception as e:
                print(f"[MACRO ADAPTER] Error running Kronos: {e}. Fallback to MOCK.")
                self._decision = self._mock_decision()
                self.out_file.write_text(json.dumps(self._decision, indent=2), encoding="utf-8")
            self._stop.wait(self.update_interval_sec)

    def _mock_decision(self):
        # P0 FIX: Safe fallback — NEUTRAL only. Never random BULL/BEAR in production.
        return {
            "bias": "NEUTRAL",
            "confidence": 0.0,
            "max_risk_multiplier": 1.0,
            "source": "SAFE_FALLBACK",
            "updated_at": int(time.time()),
        }
