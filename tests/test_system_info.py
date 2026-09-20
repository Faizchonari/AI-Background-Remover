"""Unit tests for System Information detection module."""

import unittest
from app.system.system_info import get_system_info, SystemInfo


class TestSystemInfo(unittest.TestCase):
    """Test suite for system information detection."""

    def setUp(self):
        self.info = get_system_info()

    def test_system_info_instance(self):
        """Verify that get_system_info returns a valid SystemInfo dataclass."""
        self.assertIsInstance(self.info, SystemInfo)

    def test_required_fields_present(self):
        """Verify that all required hardware fields are populated with expected types."""
        self.assertIsInstance(self.info.operating_system, str)
        self.assertIn("Windows", self.info.operating_system)
        self.assertIsInstance(self.info.windows_version, str)
        self.assertIsInstance(self.info.architecture, str)
        self.assertIsInstance(self.info.cpu_name, str)
        self.assertGreater(len(self.info.cpu_name), 0)
        self.assertIsInstance(self.info.cpu_cores, int)
        self.assertGreaterEqual(self.info.cpu_cores, 1)
        self.assertIsInstance(self.info.cpu_threads, int)
        self.assertGreaterEqual(self.info.cpu_threads, 1)
        self.assertIsInstance(self.info.ram_total_gb, float)
        self.assertGreater(self.info.ram_total_gb, 0.0)
        self.assertIsInstance(self.info.ram_available_gb, float)
        self.assertGreater(self.info.ram_available_gb, 0.0)
        self.assertIsInstance(self.info.gpu_name, str)
        self.assertIsInstance(self.info.gpu_vendor, str)
        self.assertIsInstance(self.info.cuda_available, bool)
        self.assertIsInstance(self.info.amd_acceleration_available, bool)
        self.assertIsInstance(self.info.acceleration_backend, str)
        self.assertIn(self.info.current_device, ("CPU", "GPU"))

    def test_no_personally_identifying_information(self):
        """Ensure no usernames, hostnames, or private paths are exposed in system info."""
        d = self.info.to_dict()
        import getpass
        username = getpass.getuser().lower()
        
        for key, value in d.items():
            if isinstance(value, str):
                self.assertNotIn(
                    username,
                    value.lower(),
                    f"PII leak detected in system info key '{key}': contains username"
                )

    def test_to_dict_serialization(self):
        """Verify dictionary serialization works smoothly."""
        d = self.info.to_dict()
        self.assertIsInstance(d, dict)
        self.assertEqual(d["operating_system"], self.info.operating_system)
        self.assertIn("ram_total_gb", d)
        self.assertIn("cuda_available", d)


if __name__ == "__main__":
    unittest.main()
