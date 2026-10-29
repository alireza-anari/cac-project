"""Isolated real settings imports; these configuration tests do not query a DB."""
import os
import subprocess
import sys
import unittest

class SettingsTests(unittest.TestCase):
    def startup(self, **values):
        env = {k:v for k,v in os.environ.items() if k not in ['CAC_DJANGO_SECRET','CAC_EXPERIMENTAL_DISPOSABLE','CAC_TEST_CONFIG']}
        env.update(values)
        return subprocess.run([sys.executable,'-c','import config.settings'],env=env,capture_output=True,text=True)
    def test_missing_secret_refuses_non_disposable_startup(self):
        result=self.startup()
        self.assertNotEqual(result.returncode,0)
        self.assertIn('CAC_DJANGO_SECRET',result.stderr)
    def test_empty_secret_and_nonexact_disposable_flags_refused(self):
        for flag in ['','0','true','yes']:
            with self.subTest(flag=flag):
                result=self.startup(CAC_DJANGO_SECRET='',CAC_EXPERIMENTAL_DISPOSABLE=flag)
                self.assertNotEqual(result.returncode,0)
                self.assertIn('CAC_DJANGO_SECRET',result.stderr)
    def test_explicit_disposable_startup_allowed(self):
        self.assertEqual(self.startup(CAC_EXPERIMENTAL_DISPOSABLE='1').returncode,0)
    def test_explicit_secret_startup_allowed(self):
        self.assertEqual(self.startup(CAC_DJANGO_SECRET='synthetic-subprocess-test-only').returncode,0)
