import json
from pathlib import Path
import shutil
import subprocess
import unittest


class GeometryConsumerTests(unittest.TestCase):
    def test_production_geometry_letterbox_and_capture_limits(self):
        root = Path(__file__).resolve().parents[2]
        process = subprocess.run([shutil.which("node"), str(root / "tools/integration/ocr-geometry-check.mjs")], cwd=root, capture_output=True, text=True, timeout=20)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(len(json.loads(process.stdout)["checks"]), 7)
