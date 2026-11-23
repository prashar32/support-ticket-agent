from agent.cli import main


def test_cli_parses_commands():
    assert main(["status"]) == 0
