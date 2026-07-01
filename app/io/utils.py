from __future__ import annotations

from pathlib import Path
from typing import Iterable
import logging

from tqdm import tqdm


logger = logging.getLogger("sig_fdsu.io")


def iter_with_progress(iterable: Iterable, desc: str = "Processing", disable: bool = False):
    return tqdm(iterable, desc=desc, disable=disable)


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
