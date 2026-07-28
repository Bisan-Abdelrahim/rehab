import importlib.util
import os
import unittest


MODULE_PATH = os.path.join(
    os.path.dirname(__file__),
    "emergency_controller.py",
)

spec = importlib.util.spec_from_file_location(
    "emergency_controller",
    MODULE_PATH,
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class EmergencyControllerTests(unittest.TestCase):
    def test_emergency_stop_clears_queue_and_blocks_new_commands(self):
        controller = module.EmergencyController(enable_pins=[])

        controller.queue_command("exercise:open")
        controller.queue_command("exercise:release")

        self.assertTrue(controller.accept_command("exercise:open"))

        controller.activate_emergency("test")

        self.assertTrue(controller.is_emergency_active)
        self.assertEqual(controller.pending_commands, [])
        self.assertFalse(controller.accept_command("exercise:hook"))

    def test_reset_emergency_reenables_controls_without_auto_restart(self):
        controller = module.EmergencyController(enable_pins=[])
        controller.activate_emergency("test")

        self.assertTrue(controller.is_emergency_active)

        controller.reset_emergency()

        self.assertFalse(controller.is_emergency_active)
        self.assertTrue(controller.accept_command("exercise:open"))
        self.assertFalse(controller.auto_restart_pending)


if __name__ == "__main__":
    unittest.main()
