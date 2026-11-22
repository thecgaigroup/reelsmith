#!/usr/bin/env python3
"""Test opencv-python version compatibility.

Verifies that opencv-python 4.x is installed and cv2.CascadeClassifier is available.
This prevents regressions from opencv-python 5.x which removed cv2.CascadeClassifier.
"""
import sys
import unittest


class TestOpenCVVersion(unittest.TestCase):
    """Test opencv-python 4.x compatibility."""
    
    def test_opencv_4x_installed(self):
        """Verify opencv-python 4.x is installed (not 5.x)."""
        try:
            import cv2
        except ImportError:
            self.skipTest("opencv-python not installed (optional dependency)")
        
        version = cv2.__version__
        major_version = int(version.split('.')[0])
        
        self.assertEqual(major_version, 4,
                        f"opencv-python {version} installed, but 4.x required (5.x removed cv2.CascadeClassifier)")
    
    def test_cascade_classifier_available(self):
        """Verify cv2.CascadeClassifier exists (removed in opencv 5.x)."""
        try:
            import cv2
        except ImportError:
            self.skipTest("opencv-python not installed (optional dependency)")
        
        self.assertTrue(hasattr(cv2, 'CascadeClassifier'),
                       "cv2.CascadeClassifier not available (opencv 5.x regression)")
    
    def test_haar_cascade_loadable(self):
        """Verify Haar cascade XML files are loadable."""
        try:
            import cv2
        except ImportError:
            self.skipTest("opencv-python not installed (optional dependency)")
        
        # Test loading the frontal face Haar cascade used by facetrack.py
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        
        try:
            cascade = cv2.CascadeClassifier(cascade_path)
            self.assertFalse(cascade.empty(),
                           f"Haar cascade loaded but is empty: {cascade_path}")
        except Exception as exc:
            self.fail(f"Failed to load Haar cascade {cascade_path}: {exc}")


def main():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
