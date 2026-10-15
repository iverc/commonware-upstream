"""Confirm targeted regressions fail on the unmodified upstream implementation."""
import json
import os
from pathlib import Path
import subprocess

CASES = [
    ("commonware-storage", "reports_reached_target_before_queued_update",
     "a queued update hid a reached target from the coordinator"),
    ("commonware-storage", "test_prune_cleans_lookup_index", "panicked at"),
    ("commonware-glue", "verification_retries_pending_final_epoch_info",
     "verification remained stuck after epoch info became available"),
]

def main():
    logs = Path(os.environ["RUNNER_TEMP"]) / "vera-upstream-baseline"
    logs.mkdir(exist_ok=True)
    for package, name, expected in CASES:
        result = subprocess.run(
            ["cargo", "nextest", "run", "--locked", "-p", package,
             "--ignore-default-filter", "--no-capture", name],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        (logs / (name + ".log")).write_text(result.stdout)
        reproduced = (result.returncode != 0 and expected in result.stdout
                      and "FAIL" in result.stdout and "error[E" not in result.stdout)
        print(json.dumps({"test": name, "status": result.returncode,
                          "reproduced": reproduced}), flush=True)
        if not reproduced:
            print("\n".join(result.stdout.splitlines()[-50:]))
            raise RuntimeError("upstream baseline did not reproduce the expected failure")

if __name__ == "__main__":
    main()
