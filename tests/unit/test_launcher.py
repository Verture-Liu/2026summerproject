from research_agent.launcher import build_parser, find_free_port


def test_find_free_port_returns_bindable_port():
    port = find_free_port()
    assert 1024 < port < 65536


def test_launcher_parser_supports_no_browser():
    args = build_parser().parse_args(["--no-browser", "--port", "8123"])
    assert args.no_browser is True
    assert args.port == 8123
