import unittest
from unittest.mock import MagicMock, patch

import src.process  # noqa: F401 - ensure module is imported before patching


class TestProcessControl(unittest.TestCase):
    @patch("src.process.psutil.process_iter")
    def test_is_running_true(self, mock_iter):
        mock_iter.return_value = [MagicMock(info={"name": "Antigravity.exe"})]
        self.assertTrue(src.process.is_running())

    @patch("src.process.psutil.process_iter")
    def test_is_running_false(self, mock_iter):
        mock_iter.return_value = [MagicMock(info={"name": "chrome.exe"})]
        self.assertFalse(src.process.is_running())

    @patch("src.process.psutil.wait_procs", return_value=([], []))
    @patch("src.process.psutil.process_iter")
    def test_close_terminates(self, mock_iter, mock_wait):
        proc = MagicMock(info={"name": "Antigravity.exe"})
        mock_iter.return_value = [proc]
        self.assertTrue(src.process.close())
        proc.terminate.assert_called_once()

    @patch("src.process.psutil.process_iter")
    def test_close_not_running(self, mock_iter):
        mock_iter.return_value = []
        self.assertFalse(src.process.close())


if __name__ == "__main__":
    unittest.main()
