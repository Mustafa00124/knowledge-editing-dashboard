from typing import Any, Dict, List

from pydantic import BaseModel


class SubmitExperimentRequest(BaseModel):
    experiment_type: str
    save_results: bool = True
    # Every field arrives as a list, even single-value ones - a plain
    # submission is just a sweep of size 1 per field. See slurm.submit_sweep.
    params: Dict[str, List[Any]] = {}


class ArchiveRequest(BaseModel):
    runs: List[str] = []
    reason: str = ""
    # Ask what would move without moving anything - what the confirmation
    # dialog shows before you commit.
    dry_run: bool = False


class DownloadItem(BaseModel):
    kind: str  # "dataset", "model" or "component"
    name: str
    # Optional pieces of a dataset, e.g. ["train"] for UniEdit's train split.
    parts: List[str] = []


class DownloadRequest(BaseModel):
    items: List[DownloadItem]
