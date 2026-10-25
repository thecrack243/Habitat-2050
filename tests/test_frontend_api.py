"""Contract and HTTP checks for the separate React frontend's local API."""

import json
from pathlib import Path
import sys
from threading import Thread
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer
from zipfile import ZipFile
from io import BytesIO


ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "fronten-2"))

from api.server import DashboardHandler


class FrontendApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), DashboardHandler)
        cls.server.daemon_threads = True
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_dashboard_response_matches_python_pipeline(self):
        with urlopen(f"{self.base_url}/api/dashboard", timeout=30) as response:
            payload = json.loads(response.read())

        self.assertEqual(len(payload["cells"]), 2268)
        self.assertEqual(payload["evaluation"]["presence_cells"], 34)
        self.assertEqual(payload["evaluation"]["validation_cells"], 34)
        self.assertEqual(payload["audit_counts"]["retained"], 34)
        self.assertNotIn("truth_auc.csv", payload["source_sha256"])
        cell = payload["cells"][0]
        self.assertEqual(len(cell["current_factors"]), 5)
        for feature in ("elevation_m", "ndvi_growing_season", "forest_cover_pct"):
            self.assertEqual(cell["current_factors"][feature], cell["future_factors"][feature])
        self.assertNotEqual(
            cell["current_factors"]["bio1_annual_mean_temp_degC"],
            cell["future_factors"]["bio1_annual_mean_temp_degC"],
        )
        self.assertIn(cell["change_class"], {
            "stable_suitable", "lost", "gained", "stable_unsuitable",
        })

    def test_health_endpoint_confirms_local_api_readiness(self):
        with urlopen(f"{self.base_url}/api/health", timeout=10) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(json.loads(response.read()), {"status": "ok"})

    def test_invalid_threshold_is_reported_as_bad_request(self):
        request = Request(
            f"{self.base_url}/api/export",
            data=b'{"threshold":1.2}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as error:
            urlopen(request, timeout=30)
        self.assertEqual(error.exception.code, 400)
        body = json.loads(error.exception.read())
        self.assertIn("Threshold", body["error"])

    def test_export_returns_a_self_describing_zip(self):
        request = Request(
            f"{self.base_url}/api/export",
            data=b'{"threshold":0.65}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=30) as response:
            content = response.read()
            self.assertEqual(response.headers.get_content_type(), "application/zip")
        with ZipFile(BytesIO(content)) as archive:
            metadata = json.loads(archive.read("evaluation.json"))
            self.assertEqual(metadata["export_summary"]["threshold"], 0.65)
            self.assertEqual(len(archive.namelist()), 9)
            self.assertIn("cells.geojson", archive.namelist())

    def test_unknown_endpoint_is_not_hidden_as_success(self):
        with self.assertRaises(HTTPError) as error:
            urlopen(f"{self.base_url}/api/not-a-route", timeout=10)
        self.assertEqual(error.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
