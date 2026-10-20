"""Console entry point: `fmod-studio-mcp [--doctor [--json] | --version]`.

Handles the diagnostic flags before importing fmod_mcp.main, which builds the
MCP server and registers every tool at import time; with no flags it runs the
stdio server exactly as before.
"""

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="fmod-studio-mcp",
        description="MCP server for FMOD Studio. Run with no arguments to serve over stdio.",
    )
    parser.add_argument("--doctor", action="store_true",
                        help="check this machine's setup (Studio, project, Script Server, ffmpeg) and exit")
    parser.add_argument("--json", action="store_true", help="with --doctor: print JSON")
    parser.add_argument("--version", action="store_true", help="print the package version and exit")
    args = parser.parse_args()

    if args.version or args.doctor:
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8")
        from fmod_mcp import doctor

        if args.version:
            print(doctor.package_version())
            return
        sys.exit(doctor.main(as_json=args.json))

    from fmod_mcp.main import main as serve

    serve()


if __name__ == "__main__":
    main()
