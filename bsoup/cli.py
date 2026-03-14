"""Command-line interface for bsoup."""

import argparse
import asyncio
import json
import os
import time
from typing import Optional

from .scraper import VERSION, Scraper


def get_output_path(local: bool, script_dir: str) -> str:
    """Determine the directory where the CSV file will be written.

    Args:
        local: When ``True`` the script directory is used.  Otherwise the
            function tries to locate the user's Desktop folder.
        script_dir: Absolute path of the calling script's directory, used
            when *local* is ``True``.

    Returns:
        Absolute path to the chosen output directory.
    """
    if local:
        return script_dir

    home = os.path.expanduser('~')
    desktop: Optional[str] = None

    if os.name == 'nt':
        desktop = os.path.join(os.environ.get('USERPROFILE', home), 'Desktop')
    else:
        # Try XDG user-dirs config for localised Desktop path
        try:
            cfg = os.path.join(home, '.config', 'user-dirs.dirs')
            with open(cfg, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('XDG_DESKTOP_DIR'):
                        path = line.split('=', 1)[1].strip().strip('"')
                        desktop = path.replace('$HOME', home)
                        break
        except Exception:
            pass
        if not desktop:
            desktop = os.path.join(home, 'Desktop')

    return desktop if os.path.exists(desktop) else home


def main() -> None:
    """Entry point for the bsoup CLI."""
    parser = argparse.ArgumentParser(
        description="Fetch financial data from Boursorama URLs and save to a CSV file."
    )
    parser.add_argument(
        '-l', '--local',
        action='store_true',
        help="Create the CSV file in the local directory instead of the desktop.",
    )
    parser.add_argument(
        '-f', '--file',
        type=str,
        default='urls.json',
        help="JSON file to use (default: urls.json)",
    )
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'bsoup {VERSION}',
    )
    parser.add_argument(
        '-s', '--sep',
        choices=['.', ','],
        default='.',
        help="Decimal separator for CSV values (default: '.')",
    )
    args = parser.parse_args()

    try:
        with open(args.file, 'r', encoding='utf-8') as file:
            urls_list = json.load(file)
    except FileNotFoundError:
        print(f"The file '{args.file}' was not found.")
        raise SystemExit(1)
    except json.JSONDecodeError:
        print(f"Error decoding the JSON file '{args.file}'.")
        raise SystemExit(1)

    if not isinstance(urls_list, list) or not all(len(item) == 3 for item in urls_list):
        print("Invalid JSON format. Expected a list of [URL, indice_name, is_enabled].")
        raise SystemExit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = get_output_path(args.local, script_dir)

    start_time = time.time()
    scraper = Scraper(decimal_sep=args.sep)
    asyncio.run(
        scraper.scrape_to_csv(urls_list, output_dir=output_dir, filename_suffix=args.file)
    )
    end_time = time.time()
    print(f"\nDuration: {end_time - start_time:.2f} sec")


if __name__ == "__main__":
    main()
