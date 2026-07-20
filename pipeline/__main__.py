import argparse
import sys

def main():
    parser = argparse.ArgumentParser(description="Blinkit Discovery Engine Pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # run command
    run_parser = subparsers.add_parser("run", help="Run the pipeline")
    run_parser.add_argument("--sources", type=str, default="tier1", help="Sources to ingest (e.g., tier1, all, reddit)")
    run_parser.add_argument("--limit", type=int, default=100, help="Limit items per source")
    
    # audit-filter command
    audit_parser = subparsers.add_parser("audit-filter", help="Spot-check relevance filter output")
    
    args = parser.parse_args()

    if args.command == "run":
        print(f"Running pipeline for sources: {args.sources} with limit {args.limit}")
        # TODO: wire up actual pipeline execution
    elif args.command == "audit-filter":
        print("Running filter audit...")
        # TODO: wire up audit logic
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
