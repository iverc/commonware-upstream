import pathlib
import subprocess

cases = {
    'test_prune_visits_each_translated_bucket_once': 'one affected bucket required',
    'retain_compacts_collisions_linearly': 'retaining 128 entries shifted 4032 elements',
    'single_state_sync_drains_progress_while_target_send_is_blocked': 'single-database sync deadlocked on target/progress backpressure',
}
for name, expected in cases.items():
    command = ['cargo', 'nextest', 'run', '--locked', '-p', 'commonware-storage', '-p', 'commonware-glue',
               '--ignore-default-filter', '--failure-output', 'immediate', '-E', f'test(::{name})']
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    pathlib.Path(f'review-regression-{name}.log').write_text(result.stdout)
    print(result.stdout, flush=True)
    if result.returncode != 100 or expected not in result.stdout or '1 failed' not in result.stdout:
        raise SystemExit(f'{name}: expected assertion was not reproduced (exit {result.returncode})')
    print(f'Confirmed original defect: {name}', flush=True)
