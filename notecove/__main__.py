import argparse
import json

from notecove.index import Index
from notecove.ingest import ingest_folder


def main():
    parser = argparse.ArgumentParser(description="Search a local collection of notes")
    parser.add_argument("--db", default="notes.sqlite3")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest")
    ingest.add_argument("folder")
    search = commands.add_parser("search")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=5)
    commands.add_parser("documents")
    args = parser.parse_args()
    index = Index(args.db)
    try:
        if args.command == "ingest":
            result = ingest_folder(index, args.folder)
        elif args.command == "search":
            result = index.search(args.query, args.limit)
        else:
            result = index.documents()
        print(json.dumps(result, indent=2))
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + "\n")
    finally:
        index.close()


if __name__ == "__main__":
    main()
