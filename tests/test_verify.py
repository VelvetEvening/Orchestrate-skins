import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from verify import verify


class VerifyTests(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        self.root = Path(workspace.name)
        self.package = self.root / "themes" / "example"
        self.package.mkdir(parents=True)
        self.entry = {"id": "example", "name": "Example"}
        self.write_catalog(self.entry)
        self.write_theme()

    def write_catalog(self, *entries):
        self.write_json(self.root / "catalog.json", {"schemaVersion": 1, "themes": entries})

    def write_theme(self, **fields):
        self.write_json(
            self.package / "theme.json",
            {"schemaVersion": 1, **self.entry, "base": "dark", **fields},
        )

    @staticmethod
    def write_json(path, payload):
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def test_valid_theme_with_optional_png(self):
        self.assertEqual(verify(self.root), 1)
        self.write_theme(colors={"accent": "#0022aa"}, sidebarImage="sidebar.png")
        Image.new("RGBA", (20, 20)).save(self.package / "sidebar.png")
        self.assertEqual(verify(self.root), 1)

    def test_duplicate_theme_id(self):
        self.write_catalog(self.entry, {**self.entry, "name": "Another"})
        with self.assertRaisesRegex(ValueError, "duplicate theme ID"):
            verify(self.root)

    def test_catalog_and_directory_references(self):
        self.write_catalog({"id": "missing", "name": "Missing"})
        with self.assertRaisesRegex(ValueError, "expected a theme directory"):
            verify(self.root)
        self.write_catalog()
        with self.assertRaisesRegex(ValueError, "missing from catalog.json"):
            verify(self.root)
        self.write_catalog(self.entry)
        self.write_theme(id="different")
        with self.assertRaisesRegex(ValueError, "theme ID must match"):
            verify(self.root)
        self.write_theme(name="Different")
        with self.assertRaisesRegex(ValueError, "theme name must match"):
            verify(self.root)

    def test_invalid_manifest(self):
        for fields in (
            {"schemaVersion": True},
            {"id": "a\n"},
            {"id": "precision"},
            {"id": "com0"},
            {"name": " Example"},
            {"name": "Example\u200b"},
            {"name": "😀" * 33},
            {"base": "system"},
            {"colors": {"accent": "#112233\n"}},
            {"colors": {"accent": "rgba(0, 0, 0, 1)"}},
            {"colors": {"wrong": "#123456"}},
            {"sidebarImage": "../sidebar.png"},
        ):
            with self.subTest(fields=fields):
                self.write_theme(**fields)
                with self.assertRaises(ValueError):
                    verify(self.root)

    def test_invalid_json(self):
        catalog = self.root / "catalog.json"
        catalog.write_text('{"schemaVersion": 1, "themes": [], "themes": []}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate key"):
            verify(self.root)
        catalog.write_text('{"schemaVersion": 1, "themes": [], "unknownField": NaN}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid JSON value"):
            verify(self.root)

    def test_invalid_sidebar(self):
        self.write_theme(sidebarImage="sidebar.png")
        sidebar = self.package / "sidebar.png"
        with self.assertRaisesRegex(ValueError, "expected a regular file"):
            verify(self.root)
        sidebar.write_bytes(b"PNG")
        with self.assertRaisesRegex(ValueError, "sidebar.png"):
            verify(self.root)
        Image.new("RGBA", (4097, 1)).save(sidebar)
        with self.assertRaisesRegex(ValueError, "dimensions exceed"):
            verify(self.root)
        Image.new("RGBA", (2049, 2048)).save(sidebar)
        with self.assertRaisesRegex(ValueError, "dimensions exceed"):
            verify(self.root)
