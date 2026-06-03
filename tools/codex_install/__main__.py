"""CLI: python -m codex_install --source <repo> --dest <~/.codex> [--force]."""
from __future__ import annotations

import argparse
from pathlib import Path

from codex_install.installer import install


def main(argv=None):
    repo_default = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(prog="codex_install")
    parser.add_argument("--source", default=str(repo_default),
                        help="css-claude repo root (default: inferred)")
    parser.add_argument("--dest", default=str(Path.home() / ".codex"),
                        help="Codex home (default: ~/.codex)")
    parser.add_argument("--force", action="store_true",
                        help="overwrite existing config.json")
    args = parser.parse_args(argv)
    summary = install(args.source, args.dest, force=args.force)
    print(f"Installed {summary['commands']} prompts, {summary['agents']} agents "
          f"into {args.dest}")
    print(f"  config.json {'written' if summary['config_written'] else 'kept (exists)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
