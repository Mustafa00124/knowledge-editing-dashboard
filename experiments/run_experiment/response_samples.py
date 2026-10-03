"""Qualitative responses using the same method path as evaluation."""


def method_samples(model, tok, requests, device, method, step, hparams, index=None):
    from eval_utils import sample_generations

    # A true unedited baseline must not inject IKE's new fact either.
    if step == 0 or method not in ("ike", "scr"):
        samples = sample_generations(model, tok, [r["prompt"] for r in requests], device)
    else:
        if index is None:
            raise ValueError("In-context samples require the current retrieval index")
        model.eval()
        samples = []
        for record in requests[:3]:
            prompt = record["prompt"]
            if method == "ike":
                from ike import ike_answer

                answer = ike_answer(model, tok, f"{prompt} {record['target_new']}",
                                    prompt, index, device, hparams.k, hparams.max_new_tokens)
            else:
                from scr import scr_answer

                answer = scr_answer(model, tok, prompt, index, device,
                                    hparams.retrieval_k, hparams.max_new_tokens, hparams)
            samples.append({"prompt": prompt, "continuation": answer})
    for sample in samples:
        sample["sampling_version"] = 2
        sample["generation_method"] = "baseline" if step == 0 else method
    return samples
