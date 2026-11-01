import subprocess
import sys

import pytest
from diff_pdf_visually import diff, external_programs
from diff_pdf_visually.report import write_report


@pytest.mark.parametrize('score, expected', [(19.9, [1]), (20, []), (20.1, [])])
def test_threshold_boundary(tmp_path, monkeypatch, capsys, score, expected):
    source = tmp_path / 'input.pdf'
    source.touch()
    monkeypatch.setattr(diff, 'pdftopng', lambda *a, **kw: ['1'])
    monkeypatch.setattr(diff, 'imgdiff', lambda *a, **kw: score)
    assert diff.pdfdiff_pages(source, source, threshold=20) == expected
    assert ('The PDFs are different.' if expected else 'The PDFs are the same.') in capsys.readouterr().out


@pytest.mark.parametrize('quoted', [False, True])
def test_executable_path_with_spaces(tmp_path, monkeypatch, quoted):
    executable = tmp_path / 'Program Files' / 'compare.exe'
    executable.parent.mkdir()
    executable.touch()
    monkeypatch.setenv('COMPARE', '"{}"'.format(executable) if quoted else str(executable))
    monkeypatch.setattr(external_programs, '_COMPARE_CMD', None)
    commands = []
    def run(print_cmds, args, **kw):
        commands.append(args)
        return subprocess.CompletedProcess(args, 0)
    monkeypatch.setattr(external_programs, 'verbose_run', run)
    assert external_programs.compare_cmd(False) == [str(executable)]
    assert commands == [[str(executable), '-version']]


@pytest.mark.parametrize('args', [
    ['--dpi', '0'], ['--time', '-1'], ['--threshold', 'nan'],
    ['-q', '-v'], ['-qq'], ['-vvv'], ['--outdir', 'missing-directory'],
])
def test_cli_validation_without_assertions(args):
    result = subprocess.run([sys.executable, '-O', '-m', 'diff_pdf_visually',
                             'tests/base.pdf', 'tests/base.pdf'] + args,
                            capture_output=True, text=True)
    assert result.returncode == 2
    assert 'error:' in result.stderr
    assert 'Traceback' not in result.stderr


def test_report_escapes_names_and_handles_absent_pages(tmp_path):
    write_report(tmp_path, '<before>.pdf', 'after.pdf', ['1'], ['1', '2'], {}, 100)
    report = (tmp_path / 'index.html').read_text(encoding='utf-8')
    assert '&lt;before&gt;.pdf' in report
    assert 'Page 1 — Not compared' in report
    assert 'Page 2 — Added' in report


def test_report_is_retained_with_real_comparison(tmp_path):
    assert diff.pdfdiff_pages('tests/base.pdf', 'tests/base.pdf', tempdir=tmp_path, verbosity=0) == []
    report = (tmp_path / 'index.html').read_text(encoding='utf-8')
    assert 'Page 1 — Unchanged' in report
    assert 'src="diff-1.png"' in report


def test_report_matches_different_page_number_padding(tmp_path):
    (tmp_path / 'a-1.png').touch()
    (tmp_path / 'b-01.png').touch()
    write_report(tmp_path, 'a.pdf', 'b.pdf', ['1'], ['01', '02'], {}, 100)
    report = (tmp_path / 'index.html').read_text(encoding='utf-8')
    assert report.count('Page 1 —') == 1
    assert 'src="a-1.png"' in report
    assert 'src="b-01.png"' in report


def test_cli_reports_dependency_errors(monkeypatch, capsys):
    from diff_pdf_visually import __main__ as cli
    monkeypatch.setattr(sys, 'argv', ['diff-pdf-visually', 'tests/base.pdf', 'tests/base.pdf'])
    def fail(*args, **kwargs):
        raise FileNotFoundError('pdftocairo is missing')
    monkeypatch.setattr(cli, 'pdf_similar', fail)
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 1
    assert capsys.readouterr().err == 'error: pdftocairo is missing\n'
