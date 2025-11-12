import unittest

from transition.web.app import app


class TestUiIntegration(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_preview_template(self):
        response = self.client.get('/preview')
        self.assertEqual(response.status_code, 200)
        self.assertIn('معاينة ديناميكية'.encode('utf-8'), response.data)

    def test_reports_template(self):
        response = self.client.get('/reports')
        self.assertEqual(response.status_code, 200)
        self.assertIn('تقارير'.encode('utf-8'), response.data)


if __name__ == '__main__':
    unittest.main()
