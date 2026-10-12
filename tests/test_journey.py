"""Exercise stage boundaries using fake tools; no network or wallet state."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]

class JourneyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'scripts').mkdir()
        shutil.copy(SOURCE / 'scripts/journey.sh', self.root / 'scripts')
        shutil.copy(SOURCE / 'setup.sh', self.root)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.log = self.root / 'calls'
        self.env = dict(os.environ, PATH=f'{self.bin}:/usr/bin:/bin', CALLS=str(self.log))
        for d in ['project-template/integration', 'frontend-template/node_modules',
                  'project-template/contracts/counter-account',
                  'project-template/contracts/increment-note']:
            (self.root / d).mkdir(parents=True)
        (self.root / 'project-template/miden-toolchain.toml').write_text('[toolchain]\nchannel = "0.17.0"\n')
        for name in ['counter-account', 'increment-note']:
            (self.root / f'project-template/contracts/{name}/Cargo.toml').touch()
        for name in ['cargo', 'rustc', 'miden', 'midenup', 'yarn', 'node', 'git']:
            self.tool(name)

    def tool(self, name, body='exit 0'):
        path = self.bin / name
        path.write_text(f'#!/bin/bash\nprintf "%s:%s:%s\\n" "$PWD" "{name}" "$*" >> "$CALLS"\n{body}\n')
        path.chmod(0o755)

    def run_stage(self, stage):
        return subprocess.run(['/bin/bash', str(self.root / 'scripts/journey.sh'), stage],
                              env=self.env, capture_output=True, text=True)

    def test_contracts_use_integration_directory_and_locked_resolution(self):
        self.assertEqual(self.run_stage('contracts').returncode, 0)
        self.assertIn('project-template/integration:cargo:test -p integration --release --locked', self.log.read_text())

    def test_testnet_requires_explicit_opt_in(self):
        result = self.run_stage('testnet')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('MIDEN_ALLOW_TESTNET=1', result.stderr)
        self.assertFalse(self.log.exists())

    def test_failed_contract_stage_propagates(self):
        self.tool('cargo', 'exit 7')
        self.assertEqual(self.run_stage('contracts').returncode, 7)

    def test_missing_artifacts_fail_before_handoff(self):
        self.assertNotEqual(self.run_stage('artifacts').returncode, 0)

    def test_artifacts_validate_all_inputs_before_copying(self):
        package_dir = self.root / 'frontend-template/public/packages'
        package_dir.mkdir(parents=True)
        source = self.root / 'project-template/contracts/counter-account/target/miden/release/out.masp'
        source.parent.mkdir(parents=True)
        source.write_bytes(b'counter')
        self.assertNotEqual(self.run_stage('artifacts').returncode, 0)
        self.assertFalse((package_dir / 'counter-account.masp').exists())

    def test_local_validator_requires_explicit_stage_opt_in(self):
        result = self.run_stage('local')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('MIDEN_ALLOW_LOCAL=1', result.stderr)
        self.assertFalse(self.log.exists())

    def test_setup_reports_failed_sdk_context_sync(self):
        self.tool('node', 'echo v20.20.2')
        self.tool('yarn', 'if [[ "$1" == --version ]]; then echo 1.22.22; elif [[ "$1" == miden-skills ]]; then exit 5; fi')
        result = subprocess.run(['/bin/bash', str(self.root / 'setup.sh')], env=self.env,
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('SDK context sync failed', result.stderr)

    def test_setup_installs_project_channel_and_locks_frontend(self):
        self.tool('node', 'echo v20.20.2')
        self.tool('yarn', 'if [[ "$1" == --version ]]; then echo 1.22.22; fi')
        result = subprocess.run(['/bin/bash', str(self.root / 'setup.sh')], env=self.env,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.log.read_text()
        self.assertIn('project-template:midenup:install 0.17.0', calls)
        self.assertNotIn('install stable', calls)
        self.assertIn('yarn:install --frozen-lockfile', calls)
        self.assertIn('contracts/counter-account:miden:build --release', calls)

if __name__ == '__main__':
    unittest.main()
