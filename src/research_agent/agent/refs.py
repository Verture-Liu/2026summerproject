def normalize_step_ref(ref: str) -> str:
    if "/" in ref and ref.startswith("step_"):
        step_id, output_name = ref.split("/", 1)
        if step_id and output_name:
            return f"{step_id}.{output_name}"
    if ":" in ref and ref.startswith("step_"):
        step_id, output_name = ref.split(":", 1)
        if step_id and output_name:
            return f"{step_id}.{output_name}"
    return ref
