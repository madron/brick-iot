import os
import unittest
from tempfile import TemporaryDirectory
from brick.config import get_config


class GetConfigTest(unittest.TestCase):
    def test_comment(self):
        config = """
            name: mybrick
            devices:
                random_generator:
                    type: Random
                    delay: 5
                    scale: 100
        """
        with TemporaryDirectory() as config_dir:
            config_file = os.path.join(config_dir, 'config.yml')
            with open(config_file, 'w') as f:
                f.write(config)
            config = get_config(config_dir=config_dir)

        self.assertEqual(config['name'], 'mybrick')

    def test_default(self):
        with TemporaryDirectory() as config_dir:
            config_file = os.path.join(config_dir, 'config.yml')
            config = get_config(config_dir=config_dir)

        self.assertEqual(config['name'], 'brick')
