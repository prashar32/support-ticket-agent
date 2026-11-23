"""Command line entry point: `uv run agent <command>`."""

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agent")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", help="handle all open tickets")
    sub.add_parser("status", help="show helpdesk status and journal counts")
    sub.add_parser("probe", help="read-only look at the live helpdesk")
    sub.add_parser("reset", help="reopen all practice tickets and clear the journal")
    args = parser.parse_args(argv)
    print(f"{args.command}: not implemented yet")
    return 0
