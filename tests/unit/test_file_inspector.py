from research_agent.files.inspector import inspect_file


def test_inspect_csv_returns_columns(tmp_path):
    path = tmp_path / "sample.csv"
    path.write_text("sample,value\nA,1\n", encoding="utf-8")
    summary = inspect_file(path)
    assert summary.format == "csv"
    assert summary.columns == ["sample", "value"]
