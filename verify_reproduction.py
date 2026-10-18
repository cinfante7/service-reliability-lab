"""Regenerate every current run and report, compare bytes, then write a hash manifest."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def run(*args):
    completed = subprocess.run([sys.executable, *map(str, args)], cwd=ROOT,
                               capture_output=True, text=True, check=True)
    return completed.stdout


def main():
    # Workspace-local temp avoids Windows sandbox redirecting system TEMP to an
    # unwritable package directory. tempfile owns and removes only this new child.
    with tempfile.TemporaryDirectory(prefix='.reproduce-', dir=ROOT) as folder:
        temp = Path(folder)
        for relative, seeds in [('results', [17, 29, 43]),
                                ('results/sensitivity', list(range(1, 11)))]:
            target = temp / relative
            run('reliability_lab.py', '--output', target, '--seeds', *seeds)
            for name in ('runs.json', 'runs.csv'):
                recorded = ROOT / relative / name
                if recorded.read_bytes() != (target / name).read_bytes():
                    raise AssertionError(f'Reproduction differs: {recorded}')
                print(f'PASS exact reproduction: {relative}/{name}')
    generated = [ROOT / 'results' / name for name in
                 ('report.html', 'summary.md', 'trace-example.json')]
    before = {path: path.read_bytes() for path in generated}
    run('build_report.py')
    for path, content in before.items():
        if path.read_bytes() != content:
            raise AssertionError(f'Report rebuild differs: {path}')
        print(f'PASS deterministic rebuild: {path.relative_to(ROOT).as_posix()}')
    artifacts = [ROOT / 'results' / name for name in
                 ('runs.json', 'runs.csv', 'sensitivity/runs.json', 'sensitivity/runs.csv',
                  'report.html', 'summary.md', 'trace-example.json')]
    manifest = dict(python_version=sys.version.split()[0], primary_seeds=[17, 29, 43],
                    sensitivity_seeds=list(range(1, 11)),
                    sha256={p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in artifacts})
    (ROOT / 'results/manifest.json').write_text(json.dumps(manifest, indent=2) + '\n',
                                               encoding='utf-8', newline='\n')
    print('PASS: four raw artifacts and three generated artifacts; manifest written')


if __name__ == '__main__':
    main()
