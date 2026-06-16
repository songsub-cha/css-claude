import shutil
import subprocess
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SUITE = REPO / "tests" / "gh_sync" / "test_gh_sync.sh"


class GhSyncBashSuite(unittest.TestCase):
    def test_bash_suite_passes(self):
        bash = shutil.which("bash")
        if bash is None:
            self.skipTest("bash not available")
        if not SUITE.exists():
            self.skipTest("gh_sync bash suite missing")
        proc = subprocess.run(
            [bash, str(SUITE)], cwd=str(REPO),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        self.assertEqual(
            proc.returncode, 0, msg=(proc.stdout or "") + (proc.stderr or "")
        )


if __name__ == "__main__":
    unittest.main()
