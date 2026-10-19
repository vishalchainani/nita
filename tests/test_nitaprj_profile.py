import shutil
import subprocess
import unittest
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NITAPRJ_DIR = ROOT / "utils" / "nitaprj"
NITAPRJ_SCRIPT = NITAPRJ_DIR / "nitaprj.sh"


class NitaprjProfileTests(unittest.TestCase):
    def test_jtaf_ansible_create_renders_and_packages_project_yaml(self):
        project_name = f"nitaprj-test-{uuid.uuid4().hex}"
        project_dir = NITAPRJ_DIR / project_name

        try:
            result = subprocess.run(
                ["bash", str(NITAPRJ_SCRIPT), "create", project_name, "jtaf-ansible"],
                cwd=NITAPRJ_DIR,
                input="n\n",
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            project_yaml = (project_dir / "project.yaml").read_text(encoding="utf-8")
            manifest = (project_dir / "manifest").read_text(encoding="utf-8")
            self.assertIn(f"name: {project_name}", project_yaml)
            self.assertNotIn("__PROJECT_NAME__", project_yaml)
            self.assertIn("project.yaml", manifest.splitlines())
            self.assertEqual(project_yaml.count("jenkins_url:"), 4)
            for entry in manifest.splitlines():
                entry = entry.strip()
                if entry and not entry.startswith("#"):
                    self.assertTrue((project_dir / entry).exists(), entry)
        finally:
            shutil.rmtree(project_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()