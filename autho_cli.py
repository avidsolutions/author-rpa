#!/usr/bin/env python3
"""Autho.R RPA - Natural Language Command Line Interface.

A conversational interface for automating tasks without writing code.
Just describe what you want to do in plain English.

Usage:
    python autho_cli.py              # Start interactive mode
    python autho_cli.py "read file.txt"  # Execute single command
    python autho_cli.py --help       # Show help

Examples:
    "read the file report.csv"
    "list all files in documents/"
    "fetch data from https://api.example.com"
    "create a word document called summary.docx"
"""

import sys
import os
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

# Optional: load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def print_banner():
    """Print the welcome banner."""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║     █████╗ ██╗   ██╗████████╗██╗  ██╗ ██████╗    ██████╗          ║
║    ██╔══██╗██║   ██║╚══██╔══╝██║  ██║██╔═══██╗   ██╔══██╗         ║
║    ███████║██║   ██║   ██║   ███████║██║   ██║   ██████╔╝         ║
║    ██╔══██║██║   ██║   ██║   ██╔══██║██║   ██║   ██╔══██╗         ║
║    ██║  ██║╚██████╔╝   ██║   ██║  ██║╚██████╔╝██╗██║  ██║         ║
║    ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚═╝  ╚═╝         ║
║                                                                   ║
║              Robotic Process Automation Framework                 ║
║                     by OnticWorks.io                              ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
""")


def print_help():
    """Print help information."""
    print("""
AUTHO.R - Natural Language RPA Interface
=========================================

Just type what you want to do in plain English!

EXAMPLES:
  📁 Files:
     "read the file data.txt"
     "list files in downloads/"
     "copy report.pdf to backup/"
     "delete temp.txt"

  📊 Spreadsheets:
     "read spreadsheet sales.csv"
     "open the excel file budget.xlsx"

  📄 Documents:
     "create a word document called report.docx"
     "fill out the form application.docx"
     "extract text from contract.pdf"

  🌐 Web:
     "fetch data from api.example.com"
     "scrape the page example.com/products"

  ⚙️  System:
     "status" - Show system status
     "help"   - Show this help
     "quit"   - Exit the program

TIP: Speak naturally! Say things like:
     "what's in that file?"
     "show me all the csv files"
     "grab the data from that website"
""")


def run_interactive():
    """Run the interactive CLI mode."""
    from rpa.core.nlp import NaturalLanguageInterface

    print_banner()

    # Check for API keys
    has_llm = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if has_llm:
        print("  🧠 LLM-powered natural language understanding: ENABLED")
    else:
        print("  📝 Using rule-based parsing (set OPENAI_API_KEY or ANTHROPIC_API_KEY for enhanced NLP)")

    print("\n  Type 'help' for commands, 'quit' to exit.\n")
    print("=" * 70)

    # Initialize the interface
    interface = NaturalLanguageInterface()

    while True:
        try:
            # Get user input
            command = input("\n🤖 What would you like to do?\n→ ").strip()

            if not command:
                continue

            # Check for exit commands
            if command.lower() in ["quit", "exit", "q", "bye"]:
                print("\n👋 Goodbye! Thanks for using Autho.R.\n")
                break

            # Check for help
            if command.lower() == "help":
                print_help()
                continue

            # Process the command
            print(f"\n⏳ Processing: \"{command}\"...")

            result = interface.process(command)

            if result["success"]:
                print(f"\n✅ {result['action']}")
                print("-" * 50)

                # Format the result
                output = result.get("result", "")
                if isinstance(output, list):
                    if len(output) > 20:
                        print(f"Showing first 20 of {len(output)} items:")
                        for item in output[:20]:
                            print(f"  • {item}")
                        print(f"  ... and {len(output) - 20} more")
                    else:
                        for item in output:
                            print(f"  • {item}")
                elif isinstance(output, dict):
                    import json
                    print(json.dumps(output, indent=2, default=str)[:2000])
                elif isinstance(output, str):
                    if len(output) > 2000:
                        print(output[:2000] + "\n... (truncated)")
                    else:
                        print(output)
                else:
                    print(output)
            else:
                print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
                if result.get("action"):
                    print(f"   Attempted: {result['action']}")

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!\n")
            break
        except EOFError:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")


def run_single_command(command: str):
    """Execute a single command and exit."""
    from rpa.core.nlp import NaturalLanguageInterface

    interface = NaturalLanguageInterface()
    result = interface.process(command)

    if result["success"]:
        print(f"✅ {result['action']}")
        output = result.get("result", "")
        if output:
            print(output)
    else:
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Autho.R RPA - Natural Language Automation",
        epilog="Example: python autho_cli.py \"read file report.txt\""
    )
    parser.add_argument(
        "command",
        nargs="*",
        help="Command to execute (omit for interactive mode)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="Autho.R RPA v1.0.0"
    )

    args = parser.parse_args()

    if args.command:
        # Single command mode
        command = " ".join(args.command)
        run_single_command(command)
    else:
        # Interactive mode
        run_interactive()


if __name__ == "__main__":
    main()
