from pathlib import Path
from tempfile import TemporaryDirectory

import zstandard


def main():
    project = Path(__file__).resolve().parents[1]
    archive = project / "7ldata.duckdb.zst"
    database = project / "7ldata.duckdb"
    if database.exists():
        print(f"Using existing {database.name}.")
        return
    if not archive.is_file():
        raise SystemExit(f"Download {archive.name} to the repository root first.")

    with TemporaryDirectory(prefix=".7ldata-", dir=project) as folder:
        partial = Path(folder) / database.name
        with archive.open("rb") as source, partial.open("wb") as target:
            expected_size = zstandard.frame_content_size(source.read(64))
            source.seek(0)
            _, written = zstandard.ZstdDecompressor().copy_stream(source, target)
        if written != expected_size:
            raise SystemExit(
                f"Archive is incomplete. Decoded {written:,} of {expected_size:,} bytes. "
                "Download the archive again."
            )
        partial.replace(database)
    print(f"Created {database.name} ({written:,} bytes).")


if __name__ == "__main__":
    main()
