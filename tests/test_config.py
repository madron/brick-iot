import os
import unittest
from tempfile import TemporaryDirectory
from brick.config import ConfigManager

os.environ['W1THERMSENSOR_NO_KERNEL_MODULE'] = '1'


class GetConfigTest(unittest.TestCase):
    async def test_comment(self):
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
            config = await ConfigManager(config_dir=config_dir).get()

        self.assertEqual(config['name'], 'mybrick')

    async def test_default(self):
        with TemporaryDirectory() as config_dir:
            config_file = os.path.join(config_dir, 'config.yml')
            config = await ConfigManager(config_dir=config_dir).get()

        self.assertEqual(config['name'], 'brick')

    def test_default_sync(self):
        with TemporaryDirectory() as config_dir:
            config_file = os.path.join(config_dir, 'config.yml')
            config = ConfigManager(config_dir=config_dir).get_sync()

        self.assertEqual(config['name'], 'brick')
