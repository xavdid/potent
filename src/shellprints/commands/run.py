from subprocess import CalledProcessError
from time import sleep

import typer

from shellprints.commands._types import PlanJson
from shellprints.shellprint import Shellprint

app = typer.Typer()


@app.command()
def run(path: PlanJson):
    with path.open("r+") as plan_file:
        plan = Shellprint.from_file(plan_file)

        for directory in plan.directories:
            print(f"Runnig in {directory}")
            try:
                for step in plan.steps:
                    if directory in step.completed_directories:
                        print("  skipping")
                        continue
                    print(f"  executing: {step}")
                    if step.run(directory):
                        step.completed_directories.append(directory)
                        plan.save(plan_file)
                        print("    success!")
                    else:
                        print("    fail!")
                        break

            except CalledProcessError:
                print("ERR: ")
                continue
