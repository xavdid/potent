from subprocess import CalledProcessError
from time import sleep

import typer

# from rich.live import Live
from shellprints.commands._types import PlanJson
from shellprints.shellprint import Shellprint

app = typer.Typer()


@app.command()
def run(path: PlanJson):
    with path.open("r+") as plan_file:
        plan = Shellprint.from_file(plan_file)

        for directory in plan.directories:
            print()
            if plan.directory_complete(directory):
                print(f"☑️ {directory.name}")
                # directory_spinner.ok(f"☑️ {directory.name}")
                print("  skipping all!")
                continue

            try:
                print(f"➡️ {directory.name}")
                for step in plan.steps:
                    print(f"  {step.slug}...", end="", flush=True)
                    # with [].slug}") as task_spinner:
                    if step.completed(directory):
                        print(" ☑️")
                        # task_spinner.ok("  ☑️ Skipping")
                        continue
                    success = step.run(directory)
                    plan.save(plan_file)
                    if success:
                        # plan.save(plan_file)
                        # task_spinner.ok("  OK")
                        print(" ✅")
                    else:
                        # task_spinner.fail("  FAIL")
                        print(" ❌")
                        break

            except (CalledProcessError, NotImplementedError):
                # directory_spinner.fail("ERR")
                print("    err!")
                continue
