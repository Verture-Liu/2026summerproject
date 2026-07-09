from research_agent.files.output_destination import (
    load_output_directory,
    save_output_directory,
)


def test_output_directory_is_initially_unset(tmp_path):
    assert load_output_directory(tmp_path) is None


def test_output_directory_round_trips(tmp_path):
    destination = tmp_path / "chosen"
    destination.mkdir()
    save_output_directory(tmp_path, destination)
    assert load_output_directory(tmp_path) == destination.resolve()
