import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/local_node.py'

class LocalNodeSafetyTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('local_node', SCRIPT)
        self.module = importlib.util.module_from_spec(spec)
        if not SCRIPT.exists():
            self.fail('Disposable local-node runner is not implemented')
        spec.loader.exec_module(self.module)

    def test_preserves_existing_state(self):
        with tempfile.TemporaryDirectory() as base:
            existing = Path(base) / 'user-state'
            existing.mkdir()
            sentinel = existing / 'wallet'
            sentinel.write_text('preserve')
            with self.assertRaises(FileExistsError):
                self.module.new_state(existing)
            self.assertEqual(sentinel.read_text(), 'preserve')

    def test_rejects_external_rpc(self):
        with self.assertRaises(ValueError):
            self.module.local_endpoint('https://rpc.mainnet.miden.io')

    def test_accepts_only_explicit_loopback_port(self):
        self.assertEqual(self.module.local_endpoint('http://127.0.0.1:58291'), 58291)
        for value in ['http://localhost:58291', 'http://127.0.0.1', 'http://127.0.0.1:0', 'http://127.0.0.1:58291/path']:
            with self.assertRaises(ValueError):
                self.module.local_endpoint(value)

    def test_propagates_validator_exit_code(self):
        self.assertEqual(self.module.run_validator(['/bin/sh', '-c', 'exit 7']), 7)

if __name__ == '__main__':
    unittest.main()
