"""
Tests for prediction functionality.
"""
import unittest
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.predict import predict_risk
from app.utils.categorizer import categorize_risk

class TestPredict(unittest.TestCase):
    
    def test_predict_risk(self):
        """Test risk prediction function."""
        features = {
            'ndvi_anomaly': 0.5,
            'rainfall_anomaly': 0.3,
            'food_price_inflation': 0.4
        }
        
        probability = predict_risk(features)
        
        # Probability should be between 0 and 1
        self.assertGreaterEqual(probability, 0)
        self.assertLessEqual(probability, 1)
    
    def test_categorize_risk(self):
        """Test risk categorization."""
        # Test low risk
        category = categorize_risk(0.2)
        self.assertEqual(category['label'], 'Low')
        
        # Test moderate risk
        category = categorize_risk(0.5)
        self.assertEqual(category['label'], 'Moderate')
        
        # Test high risk
        category = categorize_risk(0.8)
        self.assertEqual(category['label'], 'High')

if __name__ == '__main__':
    unittest.main()
