#!/usr/bin/env python3
"""
RPA Framework - Command Line Interface

Usage:
    python main.py [command] [options]

Commands:
    run         Run a workflow script
    demo        Run a demo showing available features
    version     Show version information
"""

import argparse
import sys
from pathlib import Path

from rpa import RPA, __version__


def demo():
    """Run a demonstration of RPA capabilities."""
    print("=" * 60)
    print("RPA Framework Demo")
    print("=" * 60)

    bot = RPA()

    print("\n1. Spreadsheet Module")
    print("-" * 40)
    print("   bot.spreadsheet.read('data.xlsx')")
    print("   bot.spreadsheet.write(data, 'output.csv')")
    print("   bot.spreadsheet.transform(df, operations)")

    print("\n2. File Module")
    print("-" * 40)
    print("   bot.files.list_files('/path', '*.pdf')")
    print("   bot.files.copy(src, dst)")
    print("   bot.files.batch_rename(dir, pattern, replacement)")
    print("   bot.files.organize_by_extension(dir)")

    print("\n3. PDF Module")
    print("-" * 40)
    print("   bot.pdf.extract_text('document.pdf')")
    print("   bot.pdf.merge(['a.pdf', 'b.pdf'], 'combined.pdf')")
    print("   bot.pdf.split('large.pdf', output_dir)")
    print("   bot.pdf.add_watermark(input, output, 'DRAFT')")

    print("\n4. Documentation Module")
    print("-" * 40)
    print("   bot.docs.create_word('report.docx', title='Report')")
    print("   bot.docs.create_from_template(template, output, data)")
    print("   bot.docs.create_markdown('doc.md', title, sections)")
    print("   bot.docs.markdown_to_html('doc.md')")

    print("\n5. Email Module")
    print("-" * 40)
    print("   bot.email.send(to='user@example.com', subject='Hi', body='...')")
    print("   bot.email.read_inbox(limit=10)")
    print("   bot.email.search(from_addr='boss@company.com')")
    print("   bot.email.download_attachments()")

    print("\n6. Web Scraper Module")
    print("-" * 40)
    print("   bot.scraper.get_soup('https://example.com')")
    print("   bot.scraper.extract_text(url, selector='article')")
    print("   bot.scraper.extract_table(url)")
    print("   bot.scraper.download_images(url, output_dir)")

    print("\n7. API Module")
    print("-" * 40)
    print("   bot.api.configure(base_url='https://api.example.com')")
    print("   bot.api.get('/users')")
    print("   bot.api.post('/data', json={'key': 'value'})")
    print("   bot.api.paginate('/items', limit=100)")

    print("\n8. Database Module")
    print("-" * 40)
    print("   bot.database.connect('sqlite:///data.db')")
    print("   bot.database.query('users', where={'active': True})")
    print("   bot.database.insert('logs', {'message': 'hello'})")
    print("   bot.database.execute('SELECT * FROM table')")

    print("\n9. Desktop Module")
    print("-" * 40)
    print("   bot.desktop.click(100, 200)")
    print("   bot.desktop.type_text('Hello World')")
    print("   bot.desktop.hotkey('ctrl', 'c')")
    print("   bot.desktop.screenshot('screen.png')")

    print("\n10. Workflow Orchestration")
    print("-" * 40)
    print("""
    workflow = bot.workflow("Daily Report")
    workflow.add_step("Fetch data", fetch_data)
    workflow.add_step("Process", process, retry_count=3)
    workflow.add_step("Send email", send_report)
    workflow.run()
    """)

    print("\n" + "=" * 60)
    print(f"RPA Framework v{__version__}")
    print("=" * 60)


def run_script(script_path: str, config_path: str = None):
    """Run a workflow script."""
    path = Path(script_path)

    if not path.exists():
        print(f"Error: Script not found: {script_path}")
        sys.exit(1)

    # Initialize RPA
    bot = RPA(config_path)

    # Execute script
    with open(path) as f:
        code = f.read()

    # Provide bot in script namespace
    exec(code, {"bot": bot, "RPA": RPA, "__name__": "__main__"})


def main():
    parser = argparse.ArgumentParser(
        description="RPA Framework - Python-based Robotic Process Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"RPA Framework {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Demo command
    subparsers.add_parser("demo", help="Run a demo showing available features")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run a workflow script")
    run_parser.add_argument("script", help="Path to workflow script")
    run_parser.add_argument(
        "--config", "-c",
        help="Path to configuration file",
        default=None,
    )

    # Version command
    subparsers.add_parser("version", help="Show version information")

    args = parser.parse_args()

    if args.command == "demo":
        demo()
    elif args.command == "run":
        run_script(args.script, args.config)
    elif args.command == "version":
        print(f"RPA Framework {__version__}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
