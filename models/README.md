# Models

Model weights live here, one directory per model, and are not tracked by git.
Download them with `python scripts/setup.py --models NAME` (see `--status` for
the names). Keep the directory names as the script creates them: the hparams
files point at `models/<name>`, and cached covariance statistics are keyed by
that name.
