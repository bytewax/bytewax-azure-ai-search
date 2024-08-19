import unittest
from my_azure_search import index_client


class TestAzureSearch(unittest.TestCase):
    def test_connection(self):
        self.assertIsNotNone(index_client)


if __name__ == "__main__":
    unittest.main()
