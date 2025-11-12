import json
import unittest
from pathlib import Path

from transition.web.app import app


class TestApiIntegration(unittest.TestCase):
    """Smoke tests for the transition Flask API."""

    def setUp(self):
        self.client = app.test_client()

    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'status': 'ok'})

    def test_convert_without_file(self):
        response = self.client.post('/api/convert')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.get_json())


if __name__ == '__main__':
    unittest.main()
