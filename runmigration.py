"""
@author axiner
@version v1.0.0
@created 2025/09/20 10:10
@abstract runmigration（更多参数请自行指定）
@description
@history
"""
import argparse
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

work_dir = Path(__file__).parent
sys.path.insert(0, str(work_dir))

cfg_path = work_dir / "app/migrations/alembic.ini"
if not cfg_path.exists():
    raise FileNotFoundError(f"alembic.ini not found at {cfg_path}")


def main():
    parser = argparse.ArgumentParser(description="Manage database migrations.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # generate
    gen_parser = subparsers.add_parser("generate", help="Autogenerate a new migration")
    gen_parser.add_argument("message", help="Migration message (required)")
    gen_parser.add_argument("--autogenerate", action="store_true", default=True,
                            help="Enable autogenerate (default: True)")

    # upgrade
    upgrade_parser = subparsers.add_parser("upgrade", help="Apply migrations up to head")
    upgrade_parser.add_argument("-m", "--message", help="Optional log message")
    upgrade_parser.add_argument("--revision", default="head", help="Revision to upgrade to (default: head)")

    # stamp
    stamp_parser = subparsers.add_parser("stamp", help="Set current revision without running migrations")
    stamp_parser.add_argument("revision", help="Revision to stamp")

    # current
    subparsers.add_parser("current", help="Show current revision")

    args = parser.parse_args()

    alembic_cfg = Config(str(cfg_path))

    try:
        if args.command == "generate":
            print(f"Generating migration: {args.message}")
            command.revision(alembic_cfg, autogenerate=args.autogenerate, message=args.message)
            print("Migration generated.")

        elif args.command == "upgrade":
            if args.message:
                print(f"[INFO] Upgrade context: {args.message}")
            print(f"Applying migrations to {args.revision}...")
            command.upgrade(alembic_cfg, args.revision)
            print(f"Upgraded to {args.revision}.")

        elif args.command == "stamp":
            print(f"Stamping revision: {args.revision}")
            command.stamp(alembic_cfg, args.revision)
            print("Revision stamped.")

        elif args.command == "current":
            print("Checking current revision...")
            command.current(alembic_cfg)

        else:
            parser.print_help()

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
