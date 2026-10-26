"""Shared paths for the Operacija Dvina content pipeline."""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"          # fetched source pages (not committed)
CONTENT = ROOT / "content"           # generated, verified content (committed)
DOCS = ROOT / "docs"                 # human-readable quest documents
