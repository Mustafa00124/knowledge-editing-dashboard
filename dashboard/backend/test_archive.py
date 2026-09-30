"""Moving runs between the live and archived trees, without touching the real results dir."""
import contextlib
import importlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

with contextlib.redirect_stdout(io.StringIO()):
    main = importlib.import_module("main")

archive = main.archive
results_reader = main.results_reader


def summary(run, **extra):
    return {"run": run, "method": "ft", "model": "qwen3-4b", "edit_succ": 50.0, **extra}


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out_root = Path(self.temp.name) / "results" / "run_experiment"
        self.runs = self.out_root / "runs"
        self.archived = self.out_root / "archive" / "runs"
        self.runs.mkdir(parents=True)

        self.patch_types = patch.object(
            main.registry, "list_experiment_types",
            return_value=[{"name": "run_experiment", "out_root": str(self.out_root)}],
        )
        self.patch_types.start()
        self.addCleanup(self.patch_types.stop)

        # No jobs at all, so nothing ever reads as busy unless a test says so.
        self.patch_jobs = patch.object(main.db, "list_jobs", return_value=[])
        self.patch_jobs.start()
        self.addCleanup(self.patch_jobs.stop)

        self.make_run("done_a", finished=True)
        self.make_run("done_b", finished=True)
        self.make_run("died", finished=False)
        self.make_run("died_rerun99_1234", finished=True)
        archive.rebuild_manifest(self.runs, self.out_root / "manifest.json")

    def make_run(self, name, finished):
        run_dir = self.runs / name
        (run_dir / "samples").mkdir(parents=True)
        (run_dir / "hparams.yaml").write_text("method: ft\nmodel: qwen3-4b\ndataset_benchmark: KnowEdit\n")
        (run_dir / "checkpoints.jsonl").write_text('{"step": 0}\n{"step": 1}\n')
        (run_dir / "samples" / "step_000000.json").write_text("{}")
        if finished:
            (run_dir / "summary.json").write_text(json.dumps(summary(name)))
        return run_dir

    def request(self, runs, reason="", dry_run=False):
        return main.ArchiveRequest(runs=runs, reason=reason, dry_run=dry_run)

    def manifest_runs(self, archived=False):
        return [row["run"] for row in results_reader.get_manifest(archived=archived)]

    # ------------------------------------------------------------ archiving

    def test_archive_moves_the_directory_and_drops_it_from_the_manifest(self):
        result = main.archive_results(self.request(["done_a"], reason="superseded"))

        self.assertTrue(result["applied"])
        self.assertEqual(result["moved"], ["done_a"])
        self.assertFalse((self.runs / "done_a").exists())
        self.assertTrue((self.archived / "done_a" / "summary.json").exists())
        # Contents travel with it, not just the summary.
        self.assertTrue((self.archived / "done_a" / "samples" / "step_000000.json").exists())
        self.assertEqual(self.manifest_runs(), ["died_rerun99_1234", "done_b"])
        self.assertEqual(self.manifest_runs(archived=True), ["done_a"])

        sidecar = json.loads((self.archived / "done_a" / "archived.json").read_text())
        self.assertEqual(sidecar["reason"], "superseded")
        self.assertEqual(sidecar["summary"]["run"], "done_a")
        self.assertTrue(sidecar["archived_at"])

        log = (self.out_root / "archive" / "log.jsonl").read_text().splitlines()
        self.assertEqual(json.loads(log[0])["action"], "archive")

    def test_a_rebuild_by_the_runner_does_not_resurrect_an_archived_run(self):
        """The whole reason this moves directories instead of editing manifest.json."""
        main.archive_results(self.request(["done_a"]))
        archive.rebuild_manifest(self.runs, self.out_root / "manifest.json")
        self.assertNotIn("done_a", self.manifest_runs())

    def test_dry_run_reports_the_move_without_making_it(self):
        result = main.archive_results(self.request(["done_a"], dry_run=True))

        self.assertFalse(result["applied"])
        self.assertEqual(result["moved"], [])
        row = result["plan"][0]
        self.assertTrue(row["ok"])
        self.assertEqual(row["files"], 4)
        self.assertEqual(row["to"], str(self.archived / "done_a"))
        self.assertTrue((self.runs / "done_a").exists())

    def test_one_bad_name_does_not_cost_the_rest_of_the_batch(self):
        result = main.archive_results(self.request(["done_a", "nope", "done_b"]))

        self.assertEqual(result["moved"], ["done_a", "done_b"])
        self.assertEqual([(r["run"], r["problem"]) for r in result["skipped"]], [("nope", "no such run")])

    def test_refuses_names_that_try_to_leave_the_runs_directory(self):
        for name in ["../manifest.json", "a/b", ".hidden", ""]:
            with self.subTest(name=name):
                result = main.archive_results(self.request([name]))
                self.assertEqual(result["moved"], [])
                self.assertIn("invalid run name", result["skipped"][0]["problem"])
        self.assertTrue((self.out_root / "manifest.json").exists())

    def test_never_overwrites_a_run_already_on_the_other_side(self):
        main.archive_results(self.request(["done_a"]))
        self.make_run("done_a", finished=True)
        (self.runs / "done_a" / "marker").write_text("live copy")

        result = main.archive_results(self.request(["done_a"]))

        self.assertEqual(result["moved"], [])
        self.assertIn("already on the other side", result["skipped"][0]["problem"])
        self.assertTrue((self.runs / "done_a" / "marker").exists())
        self.assertFalse((self.archived / "done_a" / "marker").exists())

    def test_refuses_a_run_a_slurm_job_is_still_writing(self):
        jobs = [{"job_id": "501", "run_name": "done_a"}, {"job_id": "502", "run_name": "done_b"}]
        statuses = {"501": {"state": "RUNNING"}, "502": {"state": "COMPLETED"}}
        with patch.object(main.db, "list_jobs", return_value=jobs), \
             patch.object(main.slurm, "sacct_statuses", return_value=statuses):
            result = main.archive_results(self.request(["done_a", "done_b"]))

        self.assertEqual(result["moved"], ["done_b"])
        self.assertIn("still writing", result["skipped"][0]["problem"])
        self.assertTrue((self.runs / "done_a").exists())

    def test_an_aged_out_sacct_record_does_not_pin_a_run_forever(self):
        jobs = [{"job_id": "501", "run_name": "done_a"}]
        with patch.object(main.db, "list_jobs", return_value=jobs), \
             patch.object(main.slurm, "sacct_statuses", return_value={"501": {"state": "UNKNOWN"}}):
            result = main.archive_results(self.request(["done_a"]))

        self.assertEqual(result["moved"], ["done_a"])

    def test_moves_nothing_when_slurm_cannot_be_reached(self):
        jobs = [{"job_id": "501", "run_name": "done_a"}]
        with patch.object(main.db, "list_jobs", return_value=jobs), \
             patch.object(main.slurm, "sacct_statuses", side_effect=RuntimeError("sacct is down")):
            with self.assertRaises(HTTPException) as caught:
                main.archive_results(self.request(["done_a"]))

        self.assertEqual(caught.exception.status_code, 503)
        self.assertTrue((self.runs / "done_a").exists())

    # ------------------------------------------------------------ restoring

    def test_restore_puts_a_run_back_and_returns_it_to_the_manifest(self):
        main.archive_results(self.request(["done_a"], reason="oops"))
        result = main.restore_results(self.request(["done_a"]))

        self.assertEqual(result["moved"], ["done_a"])
        self.assertTrue((self.runs / "done_a" / "summary.json").exists())
        self.assertFalse((self.runs / "done_a" / "archived.json").exists())
        self.assertFalse((self.archived / "done_a").exists())
        self.assertIn("done_a", self.manifest_runs())
        self.assertEqual(self.manifest_runs(archived=True), [])

        actions = [json.loads(line)["action"] for line in (self.out_root / "archive" / "log.jsonl").read_text().splitlines()]
        self.assertEqual(actions, ["archive", "restore"])

    # ------------------------------------------------------------ listing

    def test_archived_listing_covers_runs_that_never_wrote_a_summary(self):
        main.archive_results(self.request(["died", "done_a"], reason="failed sweep"))
        rows = {row["run"]: row for row in main.list_archived()}

        self.assertEqual(set(rows), {"died", "done_a"})
        self.assertIsNone(rows["died"]["summary"])
        self.assertEqual(rows["died"]["facts"]["method"], "ft")
        self.assertEqual(rows["died"]["checkpoints"], 2)
        self.assertEqual(rows["done_a"]["summary"]["edit_succ"], 50.0)
        self.assertEqual(rows["done_a"]["reason"], "failed sweep")

    def test_incomplete_listing_finds_the_runs_the_manifest_can_never_show(self):
        rows = main.list_incomplete()

        self.assertEqual([row["run"] for row in rows], ["died"])
        self.assertEqual(rows[0]["superseded_by"], ["died_rerun99_1234"])
        self.assertEqual(rows[0]["facts"]["dataset_benchmark"], "KnowEdit")
        self.assertTrue(rows[0]["modified_at"])

    def test_archived_runs_stay_readable_without_restoring_them(self):
        main.archive_results(self.request(["done_a"]))

        self.assertEqual(main.get_checkpoints("done_a", archived=True), [{"step": 0}, {"step": 1}])
        self.assertEqual(main.get_samples("done_a", archived=True), [0])
        self.assertEqual(main.get_checkpoints("done_a"), [])


if __name__ == "__main__":
    unittest.main()
