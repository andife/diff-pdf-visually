"""PSNR thresholds must not depend on ImageMagick's PSNR output scale."""
import math
import subprocess

import pytest

from diff_pdf_visually import diff as implementation


@pytest.mark.parametrize("mse, expected", [
    ("0 (0)", math.inf),
    ("655.35 (0.01)", 20),
    ("6.5535 (0.0001)", 40),
    ("1e-6 (1e-10)", 100),
    ("65535 (1)", 0),
])
def test_imgdiff_converts_normalized_mse_to_decibels(tmp_path, monkeypatch, mse, expected):
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    a.touch()
    b.touch()
    monkeypatch.setattr(implementation.external_programs, "compare_cmd", lambda _: ["compare"])

    def compare(print_cmds, args, stdout, stderr):
        assert args[args.index("-metric") + 1] == "MSE"
        stdout.write(("  Channel distortion: MSE\n    all: " + mse + "\n").encode())
        return subprocess.CompletedProcess(args, 0 if expected == math.inf else 1)

    monkeypatch.setattr(implementation, "verbose_run", compare)
    actual = implementation.imgdiff(a, b, tmp_path / "diff.png", tmp_path / "log.txt", False)
    assert actual == pytest.approx(expected)


@pytest.mark.parametrize("output", ["1", "1 (nan)", "1 (inf)", "1 (-0.1)"])
def test_imgdiff_rejects_invalid_mse(tmp_path, monkeypatch, output):
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    a.touch()
    b.touch()
    monkeypatch.setattr(implementation.external_programs, "compare_cmd", lambda _: ["compare"])

    def compare(print_cmds, args, stdout, stderr):
        stdout.write(("    all: " + output + "\n").encode())
        return subprocess.CompletedProcess(args, 1)

    monkeypatch.setattr(implementation, "verbose_run", compare)
    with pytest.raises(ValueError, match="ImageMagick normalized MSE"):
        implementation.imgdiff(a, b, tmp_path / "diff.png", tmp_path / "log.txt", False)
