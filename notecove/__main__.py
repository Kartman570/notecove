import argparse
import json
import sys

from notecove.export import export_chunks, check_index

from notecove.answers import answer
from notecove.evaluate import evaluate, load_cases
from notecove.models import Ollama, ModelError
from notecove.retrieval import hybrid
from notecove.vectors import Vectors

from notecove.index import Index
from notecove.ingest import ingest_folder, prune_missing


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
    commands.add_parser("stats")
    commands.add_parser("check")
    commands.add_parser("export")
    prune = commands.add_parser("prune")
    prune.add_argument("folder")
    remove = commands.add_parser("delete")
    remove.add_argument("source")
    ask = commands.add_parser("ask")
    ask.add_argument("question")
    ask.add_argument("--model")
    ask.add_argument("--endpoint", default="http://127.0.0.1:11434")
    evaluate_cmd = commands.add_parser("evaluate")
    evaluate_cmd.add_argument("cases")
    evaluate_cmd.add_argument("--k", type=int, default=3)
    for name in ("embed", "hybrid"):
        command = commands.add_parser(name)
        command.add_argument("--model", required=True)
        command.add_argument("--endpoint", default="http://127.0.0.1:11434")
        if name == "hybrid":
            command.add_argument("query")
    args = parser.parse_args()
    index = Index(args.db)
    try:
        if args.command == "ingest":
            result = ingest_folder(index, args.folder)
        elif args.command == "search":
            result = index.search(args.query, args.limit)
        elif args.command == "ask":
            model = Ollama(args.model, args.endpoint) if args.model else None
            result = answer(index, args.question, model)
        elif args.command == "evaluate":
            result = evaluate(index, load_cases(args.cases), args.k)
        elif args.command == "export":
            export_chunks(index, sys.stdout)
            return
        elif args.command == "check":
            result = check_index(index)
        elif args.command == "prune":
            result = {"removed": prune_missing(index, args.folder)}
        elif args.command == "stats":
            result = index.stats()
        elif args.command == "delete":
            result = {"deleted": index.delete(args.source)}
        elif args.command == "embed":
            result = {"embedded": Vectors(index).build(Ollama(args.model, args.endpoint))}
        elif args.command == "hybrid":
            result = hybrid(index, Vectors(index), args.query, Ollama(args.model, args.endpoint))
        else:
            result = index.documents()
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, ModelError) as error:
        parser.exit(2, str(error) + "\n")
    finally:
        index.close()


if __name__ == "__main__":
    main()
