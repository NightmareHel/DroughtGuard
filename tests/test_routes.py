"""
Tests for Flask routes.
"""
import unittest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.app import app

class TestRoutes(unittest.TestCase):
    
    def setUp(self):
        """Set up test client."""
        self.app = app.test_client()
        self.app.testing = True
    
    def test_index_route(self):
        """Test index page loads."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_api_regions(self):
        """Test regions API endpoint."""
        response = self.app.get('/api/regions')
        self.assertEqual(response.status_code, 200)
        self.assertIn('regions', response.get_json())
    
    def test_api_predict_missing_region(self):
        """Test predict endpoint without region."""
        response = self.app.post('/api/predict', 
                                 json={},
                                 content_type='application/json')
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
