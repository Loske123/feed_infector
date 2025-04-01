import unittest
import tempfile
import os
from run import parse_srt_file  # Replace 'your_script' with the actual filename

class TestParseSrtFile(unittest.TestCase):
    def setUp(self):
        """Create a temporary SRT file with sample subtitle data."""
        self.srt_file = tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8")
        self.srt_file.write("""1
    00:00:01,000 --> 00:00:04,000
    Hello, this is a test.

    2
    00:00:05,000 --> 00:00:07,000
    This is the second subtitle.
    """)
        self.srt_file.close()
    
    def test_parse_srt_file(self):
        expected_output = [
            {'start_time': 1.0, 'end_time': 4.0, 'text': 'Hello, this is a test.'},
            {'start_time': 5.0, 'end_time': 7.0, 'text': 'This is the second subtitle.'}
        ]
        result = parse_srt_file(self.srt_file.name)
        self.assertEqual(result, expected_output)
    
    def tearDown(self):
        os.remove(self.srt_file.name)

if __name__ == "__main__":
    unittest.main()