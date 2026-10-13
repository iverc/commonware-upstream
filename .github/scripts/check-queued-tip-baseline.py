"""Require the queued-tip regression to fail without the target-release fix."""
import json
import os
from pathlib import Path
import re
import subprocess


def main():
    source = Path('storage/src/qmdb/sync/engine.rs')
    original = source.read_bytes()
    release = (
        b'                if let Some(stashed) = self.stashed_target.take() {\n'
        b'                    return self.handle_event(Event::TargetUpdate(stashed)).await;\n'
        b'                }\n'
    )
    if original.count(release) != 1:
        raise RuntimeError('expected one coordinated target-release block')
    log = Path(os.environ['RUNNER_TEMP']) / 'queued-tip-baseline.log'
    try:
        source.write_bytes(original.replace(release, b''))
        with log.open('wb') as output:
            result = subprocess.run(
                ['just', 'test', '--locked', '-p', 'commonware-storage', '--no-capture',
                 'reached_coordinated_target_releases_stashed_update_without_another_tip'],
                stdout=output, stderr=subprocess.STDOUT, check=False,
            )
    finally:
        source.write_bytes(original)
    if log.stat().st_size > 4 * 1024 * 1024:
        raise RuntimeError('baseline output exceeds the diagnostic limit')
    output = re.sub(r'\x1b\[[0-9;]*m', '', log.read_text())
    expected = 'reached target kept a queued tip parked'
    errors = len(re.findall(r'error\[E\d+\]', output))
    observed = expected in output
    print(json.dumps({'status': result.returncode, 'expected_stall': observed,
                      'compiler_errors': errors}))
    if result.returncode == 0 or not observed or errors:
        raise RuntimeError('baseline did not fail at the queued-tip deadline')


if __name__ == '__main__':
    main()
