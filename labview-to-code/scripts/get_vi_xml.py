"""
Get VI XML — Export a LabVIEW VI to its XML representation.

Calls the GetVIXML.vi with the LabVIEW CLI to export the XML of a compiled
LabVIEW VI file.

Usage
-----
    python scripts/GetVIXML/get_vi_xml.py <path_to_vi>

Output
------
On success::

    <VI _name="..." ...>
      ...
    </VI>

On failure::

    ERROR
    <one or more lines describing what is wrong>

Exit codes
----------
* ``0`` — VI XML was exported successfully; XML is printed to stdout.
* ``1`` — Export failed; error details are printed to stdout.
* ``2`` — Invalid VI Path.
* ``3`` — Exception occurred.
"""

from pathlib import Path
import sys
import traceback
from time import time, sleep
from vi import VI

_TIMEOUT_SECONDS = 120


def get_vi_xml(vi_path: str) -> tuple[int, str]:
    """Export a LabVIEW VI to its XML representation.

    Parameters
    ----------
    vi_path:
        Absolute or symbolic path to the ``.vi`` file to export.

    Returns
    -------
    exit_code:
        ``0`` if the VI was exported successfully, ``1`` on failure.
    output:
        The VI XML string on success, or a human-readable error description
        on failure.
    """

    get_vi_xml_path = Path(__file__).resolve().parent / "GetVIXML.vi"
    vi = VI(get_vi_xml_path)

    try:
        vi['VI Path'] = vi_path
        vi.Run(True)

        deadline = time() + _TIMEOUT_SECONDS
        while vi.running():
            if time() > deadline:
                try:
                    vi.Abort()
                except Exception:
                    pass
                return 3, (
                    f"Timed out after {_TIMEOUT_SECONDS}s waiting for "
                    "GetVIXML.vi to finish."
                )
            sleep(0.1)

        error_code = vi['Error Code']
        output = vi['Output']

    except Exception:
        return 3, traceback.format_exc()

    return error_code, output


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) != 2:
        print(
            "Usage: python scripts/get_vi_xml.py <path_to_vi>",
            file=sys.stderr,
            flush=True,
        )
        sys.exit(2)

    vi_path = sys.argv[1]
    exit_code, output = get_vi_xml(vi_path)

    if exit_code == 0:
        # Use sys.stdout.write to avoid any print() length limits on large XML.
        sys.stdout.write(output)
        if not output.endswith("\n"):
            sys.stdout.write("\n")
        sys.stdout.flush()
        sys.exit(0)
    else:
        print("ERROR", flush=True)
        if output:
            sys.stdout.write(output)
            if not output.endswith("\n"):
                sys.stdout.write("\n")
            sys.stdout.flush()
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
