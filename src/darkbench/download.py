import gzip
import hashlib
import json
import logging
from datetime import date
from pathlib import Path

import requests

from darkbench import config

log = logging.getLogger(__name__)
MANIFEST = config.RAW_DIR / "manifest.json"


def load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return {}


def save_manifest(manifest: dict) -> None:
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True))


def md5sum(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(url: str, dest: Path) -> None:
    # Write to a temp file so an interrupted download is never mistaken for a cached one.
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=600) as response:
        response.raise_for_status()
        with tmp.open("wb") as handle:
            for chunk in response.iter_content(1 << 20):
                handle.write(chunk)
    tmp.rename(dest)


def gzip_opens(path: Path) -> bool:
    # Reading to the end validates the CRC, which catches truncated downloads.
    try:
        with gzip.open(path, "rb") as handle:
            while handle.read(1 << 22):
                pass
        return True
    except (OSError, EOFError):
        return False


def record(name: str, url: str, path: Path, manifest: dict) -> None:
    if name in manifest and manifest[name]["file"] == path.name:
        return
    manifest[name] = {
        "file": path.name,
        "url": url,
        "md5": md5sum(path),
        "bytes": path.stat().st_size,
        "download_date": date.today().isoformat(),
    }


def fetch_paginated(url: str, dest: Path) -> None:
    # UniProt's /stream endpoint is often unavailable for large results; /search pages
    # the same query with a cursor in the Link header.
    tmp = dest.with_suffix(dest.suffix + ".part")
    next_url: str | None = url
    with tmp.open("wb") as handle:
        while next_url:
            response = requests.get(next_url, timeout=600)
            response.raise_for_status()
            handle.write(response.content)
            next_url = response.links.get("next", {}).get("url")
    tmp.rename(dest)


def download_file(name: str, manifest: dict) -> Path:
    url = config.URLS[name]
    path = config.RAW_DIR / config.RAW_FILES[name]
    if path.exists():
        log.info("cached: %s", path.name)
    elif "/uniprotkb/search" in url:
        log.info("downloading %s from %s (paginated)", path.name, url)
        fetch_paginated(url, path)
    else:
        log.info("downloading %s from %s", path.name, url)
        fetch(url, path)
    record(name, url, path, manifest)
    return path


def pharos_query(query: str) -> dict:
    response = requests.post(config.URLS["pharos_graphql"], json={"query": query}, timeout=300)
    response.raise_for_status()
    payload = response.json()
    if "errors" in payload:
        raise RuntimeError(f"Pharos error: {payload['errors']}")
    return payload["data"]


def download_pharos(manifest: dict, page_size: int = 1000) -> Path:
    path = config.RAW_DIR / config.RAW_FILES["pharos_tdl"]
    if path.exists():
        log.info("cached: %s", path.name)
        return path
    version = pharos_query("{ dbVersion }")["dbVersion"]
    total = pharos_query("{ targets { count } }")["targets"]["count"]
    rows: list[str] = []
    for skip in range(0, total, page_size):
        query = f"{{ targets {{ targets(top:{page_size}, skip:{skip}) {{ uniprot sym tdl }} }} }}"
        for target in pharos_query(query)["targets"]["targets"]:
            rows.append(f"{target['uniprot']}\t{target['sym']}\t{target['tdl']}")
    log.info("Pharos targets: expected %d, fetched %d", total, len(rows))
    if len(rows) != total:
        raise RuntimeError("Pharos paging returned an unexpected number of targets")
    path.write_text("uniprot\tsym\ttdl\n" + "\n".join(rows) + "\n")
    manifest["pharos_tdl"] = {
        "file": path.name,
        "url": config.URLS["pharos_graphql"],
        "md5": md5sum(path),
        "bytes": path.stat().st_size,
        "download_date": date.today().isoformat(),
        "release": f"Pharos dbVersion {version} (current, post-T0)",
    }
    return path


def download_all() -> dict:
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    for name in ["gaf_t0", "gaf_t1", "go_obo_t0", "gene2pubmed", "uniprot_sprot_human"]:
        download_file(name, manifest)
        save_manifest(manifest)
    download_pharos(manifest)
    save_manifest(manifest)
    return manifest
