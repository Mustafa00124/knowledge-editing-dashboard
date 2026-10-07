"""Qualitative responses using the same method path as evaluation."""


def method_samples(model, tok, requests, device, method, step, hparams, index=None, record_scope=None):
    """record_scope(i): as in scr.evaluate_requests_scr, the knowledge base
    record i is asked against (--kb_size adds its own fact to distractors)."""
    from contextlib import nullcontext

    from eval_utils import sample_generations

    # A true unedited baseline must not inject IKE's new fact either.
    if step == 0 or method not in ("ike", "scr"):
        samples = sample_generations(model, tok, [r["prompt"] for r in requests], device)
    else:
        if index is None:
            raise ValueError("In-context samples require the current retrieval index")
        model.eval()
        samples = []
        for i, record in enumerate(requests[:3]):
            prompt = record["prompt"]
            if method == "ike":
                from ike import ike_answer

                answer = ike_answer(model, tok, f"{prompt} {record['target_new']}",
                                    prompt, index, device, hparams.k, hparams.max_new_tokens)
            else:
                from scr import scr_answer

                with record_scope(i) if record_scope else nullcontext():
                    answer = scr_answer(model, tok, prompt, index, device,
                                        hparams.retrieval_k, hparams.max_new_tokens, hparams)
            samples.append({"prompt": prompt, "continuation": answer})
    for sample in samples:
        sample["sampling_version"] = 2
        sample["generation_method"] = "baseline" if step == 0 else method
    return samples
