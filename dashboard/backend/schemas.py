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


class SweepRequest(BaseModel):
    investigation: str
    # method -> hparams key -> values to try
    methods: Dict[str, Dict[str, List[Any]]]
    models: List[str]
    data_paths: List[str]
    ds_size: str = "full"  # of the dev split: "full" is all of it (up to 100)
    edit_mode: str = "batch"
    seed: int = 0
    label: str = ""
    # Held-constant settings changed from their current value:
    # method -> model -> hparams key -> value, applied to every run.
    fixed: Dict[str, Dict[str, Dict[str, Any]]] = {}


class PromoteRequest(BaseModel):
    investigation: str
    sweep_id: str
    run: str


class DownloadItem(BaseModel):
    kind: str  # "dataset", "model" or "component"
    name: str
    # Optional pieces of a dataset, e.g. ["train"] for UniEdit's train split.
    parts: List[str] = []


class DownloadRequest(BaseModel):
    items: List[DownloadItem]
