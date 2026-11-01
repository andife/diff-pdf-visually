"""Static, dependency-free comparison reports for retained raster images."""
from html import escape
from pathlib import Path


def write_report(directory, a, b, before, after, scores, threshold):
    before = {int(n): n for n in before}
    after = {int(n): n for n in after}
    scores = {int(n): score for n, score in scores.items()}
    sections = []
    for number in sorted(set(before) | set(after), key=int):
        score = scores.get(number)
        status = ('Added' if number not in before else 'Removed' if number not in after
                  else 'Not compared' if score is None
                  else 'Changed' if score < threshold else 'Unchanged')
        figures = []
        for prefix, label in [('a', 'Before'), ('b', 'After'), ('diff', 'Difference')]:
            original = before.get(number) if prefix in ('a', 'diff') else after.get(number)
            name = '{}-{}.png'.format(prefix, original)
            content = ('<a href="{0}"><img loading="lazy" src="{0}" alt="{1}"></a>'.format(name, label)
                       if (directory / name).is_file() else '<p>Not available</p>')
            figures.append('<figure><figcaption>{}</figcaption>{}</figure>'.format(label, content))
        sections.append('<section><h2>Page {} — {}</h2><div>{}</div></section>'.format(int(number), status, ''.join(figures)))
    title = '{} → {}'.format(Path(a).name, Path(b).name)
    (directory / 'index.html').write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>{0}</title>'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<style>body{{font:16px system-ui;margin:24px}}section{{margin:24px 0}}'
        'section div{{display:flex;flex-wrap:wrap}}figure{{flex:1;min-width:240px;margin:4px}}'
        'img{{width:100%}}</style><h1>{0}</h1>'
        '<p>Pages are paired by position. Added or removed pages can shift subsequent comparisons. '
        'Images and this report are stored locally.</p>{1}</html>'.format(escape(title), ''.join(sections)),
        encoding='utf-8')
