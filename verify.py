import json
import sys
import unicodedata
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError
from PIL import Image


ROOT = Path(__file__).resolve().parent


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key {key!r}")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError(f"invalid JSON value {value}")


def regular_file(path, limit):
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"{path}: expected a regular file")
    if path.stat().st_size > limit:
        raise ValueError(f"{path}: exceeds {limit} bytes")


def read_json(path, limit, validator):
    regular_file(path, limit)
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_keys, parse_constant=reject_constant)
        validator.validate(value)
    except ValidationError as error:
        location = ".".join(str(part) for part in error.absolute_path)
        raise ValueError(f"{path}:{location} {error.message}") from error
    except ValueError as error:
        raise ValueError(f"{path}: {error}") from error
    return value


def verify_name(name, label):
    if len(name.encode("utf-16-le")) > 128 or any(
        unicodedata.category(character) in ("Cc", "Cf", "Zl", "Zp") for character in name
    ):
        raise ValueError(f"{label}: invalid theme name")


def verify_png(path):
    regular_file(path, 4 * 1024 * 1024)
    try:
        with Image.open(path, formats=("PNG",)) as image:
            width, height = image.size
            if max(width, height) > 4096 or width * height > 4_194_304:
                raise ValueError("dimensions exceed the sidebar image limit")
            image.verify()
        with Image.open(path, formats=("PNG",)) as image:
            image.load()
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombError) as error:
        raise ValueError(f"{path}: {error}") from error


def verify(root=ROOT):
    schema = json.loads((ROOT / "schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    catalog = read_json(
        root / "catalog.json", 256 * 1024,
        Draft202012Validator({"$ref": "#/$defs/catalog", "$defs": schema["$defs"]}),
    )
    theme_validator = Draft202012Validator({"$ref": "#/$defs/theme", "$defs": schema["$defs"]})
    packages = root / "themes"
    if packages.is_symlink() or (packages.exists() and not packages.is_dir()):
        raise ValueError(f"{packages}: expected a directory")
    ids = set()
    for entry in catalog["themes"]:
        theme_id = entry["id"]
        if theme_id in ids:
            raise ValueError(f"catalog.json: duplicate theme ID {theme_id!r}")
        ids.add(theme_id)
        verify_name(entry["name"], f"catalog.json ({theme_id})")
        directory = packages / theme_id
        if not directory.is_dir() or directory.is_symlink():
            raise ValueError(f"{directory}: expected a theme directory")
        manifest = directory / "theme.json"
        theme = read_json(manifest, 32 * 1024, theme_validator)
        if theme["id"] != theme_id:
            raise ValueError(f"{manifest}: theme ID must match the catalog and directory")
        verify_name(theme["name"], manifest)
        if theme["name"] != entry["name"]:
            raise ValueError(f"{manifest}: theme name must match the catalog")
        if "sidebarImage" in theme:
            verify_png(directory / theme["sidebarImage"])
    if packages.is_dir():
        unlisted = sorted(path.name for path in packages.iterdir() if path.is_dir() and path.name not in ids)
        if unlisted:
            raise ValueError("themes missing from catalog.json: " + ", ".join(unlisted))
    return len(ids)


if __name__ == "__main__":
    try:
        print(f"Validated {verify()} Orchestrate skins.")
    except (OSError, ValueError) as error:
        sys.exit(str(error))
