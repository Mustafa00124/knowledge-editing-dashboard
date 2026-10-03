"""Launching through the API the way an agent does, without SLURM: argument
parsing, strict fields, extra flags, dry runs, the agent token's limits,
and the progress view of launches."""
import contextlib
import importlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

with contextlib.redirect_stdout(io.StringIO()):
    main = importlib.import_module("main")


class LaunchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        patches = [
            patch.object(main.db.config, "DB_PATH", Path(self.temp.name) / "jobs.db"),
            patch.object(main.config, "INVESTIGATIONS_DIR", Path(self.temp.name) / "investigations"),
            patch.object(main.slurm, "_submit_one", side_effect=self.fake_submit),
            patch.object(main.slurm, "sacct_statuses", side_effect=lambda ids: {i: {"state": self.states.get(i, "PENDING")} for i in ids}),
            patch.object(main.slurm, "cancel_many", side_effect=lambda ids: self.cancelled.extend(ids)),
            patch.object(main.environment, "launch_blockers", return_value=[]),
            patch.object(main.hparam_sweeps, "_queue", return_value={}),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        main.db.init()
        self.submitted, self.states, self.cancelled = [], {}, []
        self.user = TestClient(main.app, headers={"x-dashboard-token": main.AUTH_TOKEN})
        self.agent = TestClient(main.app, headers={"x-dashboard-token": main.AGENT_TOKEN})

    def fake_submit(self, exp_cfg, params, run_name, out_root=None, extra_args=None, after_ok=()):
        job_id = str(9000 + len(self.submitted))
        self.submitted.append({"params": dict(params), "run_name": run_name, "extra_args": list(extra_args or [])})
        return {"job_id": job_id, "run_name": run_name, "params": params,
                "sbatch_path": "x.sbatch", "out_path": "x.out", "err_path": "x.err"}

    def launch(self, client=None, **body):
        body.setdefault("experiment_type", "neuron_tracing")
        return (client or self.agent).post("/api/experiments", json=body)

    def test_args_string_sweeps_repeated_flags(self):
        r = self.launch(label="two models", args="--model llama-3.1-8b --model qwen3-4b --n_prompts 5")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(len(self.submitted), 2)
        self.assertEqual({s["params"]["model"] for s in self.submitted}, {"llama-3.1-8b", "qwen3-4b"})
        self.assertTrue(all(s["params"]["n_prompts"] == 5 for s in self.submitted))
        self.assertEqual(r.json()["investigation"], "neuron_tracing")

    def test_unknown_field_is_an_error_not_dropped(self):
        r = self.launch(label="x", params={"model": ["qwen3-4b"], "not_a_field": [1]})
        self.assertEqual(r.status_code, 400)
        self.assertIn("not_a_field", r.text)
        self.assertIn("n_prompts", r.text)  # names the valid fields
        r = self.launch(label="x", args="--model qwen3-4b --bogus 3")
        self.assertEqual(r.status_code, 400)
        self.assertIn("extra_args", r.text)
        self.assertEqual(self.submitted, [])

    def test_extra_args_pass_through_and_mark_the_run_name(self):
        r = self.launch(label="x", args="--model qwen3-4b", extra_args=["--bogus 'a b'"])
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.submitted[0]["extra_args"], ["--bogus 'a b'"])
        self.assertRegex(self.submitted[0]["run_name"], r"_x[0-9a-f]{6}$")
        for bad in (["--run_name y"], ["--model qwen3-4b"]):
            self.assertEqual(self.launch(label="x", extra_args=bad).status_code, 400)

    def test_both_params_and_args_for_one_field(self):
        r = self.launch(label="x", params={"model": ["qwen3-4b"]}, args="--model llama-3.1-8b")
        self.assertEqual(r.status_code, 400)

    def test_dry_run_submits_nothing_and_shows_commands(self):
        r = self.launch(dry_run=True, args="--model qwen3-4b --n_prompts 7")
        self.assertEqual(r.status_code, 200, r.text)
        body = r.json()
        self.assertTrue(body["dry_run"])
        self.assertEqual(self.submitted, [])
        self.assertIn("--n_prompts 7", body["runs"][0]["command"])
        self.assertEqual(body["investigation"], "neuron_tracing")

    def test_agent_needs_a_label_and_is_recorded(self):
        self.assertEqual(self.launch(args="--model qwen3-4b").status_code, 400)
        self.assertEqual(self.launch(self.user, args="--model qwen3-4b").status_code, 200)
        self.launch(label="mine", note="why", args="--model qwen3-4b")
        jobs = {j["label"]: j for j in main.db.list_jobs()}
        self.assertEqual(jobs["mine"]["launched_by"], "agent")
        self.assertEqual(jobs["mine"]["note"], "why")
        self.assertEqual(jobs[""]["launched_by"], "user")

    def test_investigation_defaults_and_checks(self):
        r = self.launch(experiment_type="causal_tracing", label="q", args="--model qwen3-4b --format question")
        self.assertEqual(r.json()["investigation"], "tracing_formats")
        r = self.launch(experiment_type="causal_tracing", label="c", args="--model qwen3-4b")
        self.assertEqual(r.json()["investigation"], "causal_tracing")
        self.assertEqual(self.launch(label="x", investigation="nope").status_code, 400)
        r = self.launch(experiment_type="run_experiment", label="x", investigation="edit_layers")
        self.assertEqual(r.status_code, 400)
        self.assertIn("/api/hparams/sweeps", r.text)

    def test_agent_token_limits(self):
        self.assertEqual(self.agent.get("/api/whoami").json(), {"role": "agent"})
        self.assertEqual(self.agent.post("/api/hparams/promote", json={}).status_code, 403)
        self.assertEqual(self.agent.post("/api/queue/0/launch").status_code, 403)
        self.assertEqual(self.agent.post("/api/results/archive", json={}).status_code, 403)
        self.assertEqual(TestClient(main.app).get("/api/whoami").status_code, 401)

    def test_agent_cancels_only_its_own(self):
        user_launch = self.launch(self.user, args="--model qwen3-4b").json()
        agent_launch = self.launch(label="a", args="--model llama-3.1-8b").json()
        self.assertEqual(self.agent.post(f"/api/launches/{user_launch['launch_id']}/cancel").status_code, 403)
        self.assertEqual(self.agent.delete(f"/api/experiments/{user_launch['jobs'][0]['job_id']}").status_code, 403)
        r = self.agent.post(f"/api/launches/{agent_launch['launch_id']}/cancel")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(self.cancelled, [agent_launch["jobs"][0]["job_id"]])
        self.assertEqual(self.user.post(f"/api/launches/{agent_launch['launch_id']}/cancel").status_code, 200)

    def test_progress_view(self):
        r = self.launch(label="pair", args="--model llama-3.1-8b --model qwen3-4b").json()
        first, second = (j["job_id"] for j in r["jobs"])
        self.states[first] = "RUNNING"
        launches = self.user.get("/api/launches?investigation=neuron_tracing&active=true").json()
        self.assertEqual(len(launches), 1)
        launch = launches[0]
        self.assertEqual((launch["id"], launch["label"], launch["launched_by"]), (r["launch_id"], "pair", "agent"))
        self.assertEqual((launch["runs"], launch["active"]), (2, 2))
        self.assertEqual([x["job_id"] for x in launch["running"]], [first])
        self.assertEqual(launch["swept"], ["model"])
        self.assertEqual(self.user.get("/api/launches?investigation=circuit_tracing").json(), [])
        summary = self.user.get("/api/launches/summary").json()
        self.assertEqual(summary["neuron_tracing"], {"launches": 1, "running": 1, "waiting": 1, "by_agent": 1})
        self.states[first] = self.states[second] = "COMPLETED"
        self.assertEqual(self.user.get("/api/launches?active=true").json(), [])
        detail = self.user.get(f"/api/launches/{r['launch_id']}").json()
        self.assertEqual(detail["launch"]["overall"], 1.0)
        self.assertEqual(len(detail["runs"]), 2)
        self.assertEqual(self.user.get("/api/launches/nope").status_code, 404)


if __name__ == "__main__":
    unittest.main()
