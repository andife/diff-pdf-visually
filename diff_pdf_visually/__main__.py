import argparse, math, subprocess, sys
from pathlib import Path
from . import pdf_similar

from .constants import DEFAULT_THRESHOLD, DEFAULT_VERBOSITY, DEFAULT_DPI
from .constants import MAX_VERBOSITY, VERB_WARN_SANITY
import diff_pdf_visually

def main():

    description = """
    Compare two PDFs visually. The exit code is 0 if they are the same, and 2
    if there are significant differences.
    """.strip()

    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('a', metavar='a.pdf')
    parser.add_argument('b', metavar='b.pdf')
    parser.add_argument('--silent', '-q',
        action='count',
        default=0,
        help="silence output (can be used only once); the result can be found "
             "in the exit code")
    assert DEFAULT_VERBOSITY==1
    parser.add_argument('--verbose', '-v',
        action='count',
        default=0,
        help="show more information (can be used {} times)".format(
            MAX_VERBOSITY - DEFAULT_VERBOSITY))
    parser.add_argument('--threshold',
        default=DEFAULT_THRESHOLD,
        type=float,
        help="PSNR threshold to consider a change significant, "
             "higher is more sensitive (default: %(default)s)")
    parser.add_argument('--dpi',
        default=DEFAULT_DPI,
        type=int,
        help="resolution for the rasterised files (default: %(default)s)")
    parser.add_argument('--outdir',
        default=None,
        type=Path,
        help="empty output directory to hold intermediate files for comparison")
    parser.add_argument('--time',
        default=0,
        type=int,
        help="number of seconds to wait before discarding intermediate files from"
             "temporary directory, or 0 to immediately discard. Conflicts with --outdir")
    parser.add_argument('--version',
        action='version',
        version=f"%(prog)s {diff_pdf_visually.__version__}")

    args = parser.parse_args()

    if args.silent and args.verbose:
        parser.error("cannot be silent and verbose")
    if args.silent > 1 or args.verbose > MAX_VERBOSITY - DEFAULT_VERBOSITY:
        parser.error("use -q at most once or -v at most twice")
    if args.dpi < 1:
        parser.error("--dpi must be at least 1")
    if args.time < 0:
        parser.error("--time must be nonnegative")
    if not math.isfinite(args.threshold):
        parser.error("--threshold must be finite")
    for filename in (args.a, args.b):
        if not Path(filename).is_file():
            parser.error("input file does not exist: " + filename)
    if args.outdir and (not args.outdir.is_dir() or any(args.outdir.iterdir())):
        parser.error("--outdir must be an existing empty directory")

    verbosity = DEFAULT_VERBOSITY + args.verbose - args.silent

    if verbosity >= VERB_WARN_SANITY:
        if not args.a[-4:].lower() == ".pdf":
            print("Warning: {!r} does not end in .pdf.".format(args.a))
        if not args.b[-4:].lower() == ".pdf":
            print("Warning: {!r} does not end in .pdf.".format(args.b))

    if args.outdir and args.time:
        parser.error("--time cannot be combined with --outdir")

    try:
        similar = pdf_similar(args.a, args.b,
            verbosity=verbosity,
            threshold=args.threshold,
            dpi=args.dpi,
            tempdir=args.outdir,
            time_to_inspect=args.time)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        parser.exit(1, "error: {}\n".format(error))
    if similar:
        sys.exit(0)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main()
