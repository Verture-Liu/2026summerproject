from io import BytesIO

from research_agent.files.task_store import TaskStore


def test_add_input_sanitizes_filename(tmp_path):
    store = TaskStore(tmp_path)
    task_id = store.create_task()
    stored = store.add_input(task_id, "../../sample.csv", BytesIO(b"a,b\n1,2\n"))
    assert stored.path.parent.name == "inputs"
    assert stored.path.name == "sample.csv"
    assert stored.sha256
