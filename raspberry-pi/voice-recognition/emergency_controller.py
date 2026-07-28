import json
import os
import time
from typing import Any


def _parse_enable_pins(raw_value: str | None) -> list[int]:
    if not raw_value:
        return []

    pins: list[int] = []
    for item in raw_value.split(','):
        item = item.strip()
        if not item:
            continue
        try:
            pins.append(int(item))
        except ValueError:
            continue
    return pins


class EmergencyController:
    """Central emergency-stop state for motor control."""

    def __init__(self, enable_pins: list[int] | None = None) -> None:
        self.enable_pins = enable_pins or _parse_enable_pins(
            os.environ.get("EMERGENCY_ENABLE_PINS")
        )
        self.is_emergency_active = False
        self.pending_commands: list[dict[str, Any]] = []
        self.auto_restart_pending = False
        self.emergency_reason: str | None = None
        self.last_emergency_event: dict[str, Any] | None = None
        self._disabled_drivers = False

    def queue_command(self, command: Any) -> None:
        if self.is_emergency_active:
            return
        self.pending_commands.append({"command": command, "queued_at": time.time()})

    def accept_command(self, command: Any) -> bool:
        if self.is_emergency_active:
            return False
        self.queue_command(command)
        return True

    def activate_emergency(self, reason: str) -> dict[str, Any]:
        self.is_emergency_active = True
        self.emergency_reason = reason
        self.pending_commands.clear()
        self.auto_restart_pending = False
        self._disabled_drivers = False
        self._set_driver_enable(False)

        self.last_emergency_event = {
            "type": "emergency-stop",
            "reason": reason,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

        return self.last_emergency_event

    def reset_emergency(self) -> dict[str, Any]:
        self.is_emergency_active = False
        self.emergency_reason = None
        self.pending_commands.clear()
        self.auto_restart_pending = False
        self._set_driver_enable(True)
        self._disabled_drivers = False

        self.last_emergency_event = {
            "type": "emergency-reset",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

        return self.last_emergency_event

    def get_state(self) -> dict[str, Any]:
        return {
            "emergencyActive": self.is_emergency_active,
            "reason": self.emergency_reason,
            "pendingCommands": len(self.pending_commands),
            "driversDisabled": self._disabled_drivers,
            "autoRestartPending": self.auto_restart_pending,
        }

    def _set_driver_enable(self, enabled: bool) -> None:
        self._disabled_drivers = not enabled

        if not self.enable_pins:
            return

        if os.name != "nt" and os.environ.get("EMERGENCY_STOP_SIMULATE_HARDWARE") != "1":
            try:
                import RPi.GPIO as gpio
            except Exception:
                return

            gpio.setmode(gpio.BCM)
            for pin in self.enable_pins:
                gpio.setup(pin, gpio.OUT)
                gpio.output(pin, gpio.LOW if not enabled else gpio.HIGH)

    def to_json(self) -> str:
        return json.dumps(self.get_state())

    def handle_controller_command(self, command: str) -> bool:
        mode = os.environ.get("EMERGENCY_STOP_CONTROLLER_MODE", "mock")
        if mode == "mock":
            return True
        if mode == "disabled":
            return False

        return False
