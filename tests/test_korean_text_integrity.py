from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".c", ".cmake", ".css", ".h", ".html", ".md", ".py", ".sql", ".txt"}
SKIP_PARTS = {".git", ".vscode", "__pycache__"}
MOJIBAKE_CHARS = "".join(
    chr(code)
    for code in [
        0xFFFD,
        0x00C2,
        0x00C3,
        0x6FDB,
        0x5AC4,
        0x79FB,
        0x8ADB,
        0xF9E4,
        0x934B,
        0x6028,
    ]
)
MOJIBAKE_RE = re.compile("[" + re.escape(MOJIBAKE_CHARS) + "]")


class KoreanTextIntegrityTest(unittest.TestCase):
    def test_project_text_files_do_not_contain_mojibake(self):
        failures = []
        for path in ROOT.rglob("*"):
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue

            text = path.read_text(encoding="utf-8", errors="replace")
            if MOJIBAKE_RE.search(text):
                failures.append(str(path.relative_to(ROOT)))

        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
