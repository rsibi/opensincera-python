"""Entry point for `python -m opensincera`.

The Typer CLI lands at M2; until then this exits with a hint.
"""

import sys


def main() -> None:
    print(
        "opensincera CLI is not yet implemented in this development build.\n"
        "See the project README for status.",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
