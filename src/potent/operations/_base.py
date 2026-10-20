import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Annotated,
    Any,
    ClassVar,
    Literal,
    Optional,
    Self,
    cast,
    final,
    get_args,
)

from pydantic import AfterValidator, BaseModel, ConfigDict, FilePath

from potent.util import (
    DataValType,
    format_annotation,
    table_row,
    truthy_list,
)

# the only valid values in the json
Status = Literal["not-started", "failed", "completed"]
# but, we can print with more information
PrintableStatus = Status | Literal["halted"] | Literal["duplicate"]


def ensure_directory(value: Path) -> Path:
    """
    Supports both absolute path and paths with a leading `~`.
    """

    # we want to validate the incoming path, but not modify it.
    # So if validation passes, we still return the original value
    path_to_validate = value

    # relative paths
    str_path = str(value)
    if str_path.startswith("~"):
        path_to_validate = value.expanduser()

    # absolute paths must exist, just like before
    if not (path_to_validate.is_absolute() and path_to_validate.is_dir()):
        raise ValueError("path must be an absolute path to a directory that exists")

    return value


AbsDirPath = Annotated[Path, AfterValidator(ensure_directory)]


# useful for writing back absolute paths, which is good for portability
def ensure_abs_path(value: Path) -> Path:
    if not value.is_absolute():
        raise ValueError("path is not absolute")
    return value


AbsFilePath = Annotated[
    FilePath,
    AfterValidator(ensure_abs_path),
]

CONFIG_KEY = "config"


class OperationResult(BaseModel):
    """
    A struct representing the result of running an operation in a directory. Includes information about the input and output of the command.
    """

    success: bool
    output: str
    cmd: Optional[str] = None

    @staticmethod
    def from_process(
        result: subprocess.CompletedProcess[str], cmd: Optional[list[str]] = None
    ):
        command = None

        if cmd:
            command = " ".join(f'"{arg}"' if " " in arg else arg for arg in cmd)

        return OperationResult(
            success=result.returncode == 0, output=result.stdout, cmd=command
        )


LookupFunc = Callable[[str], DataValType]


@dataclass(frozen=True)
class Context:
    """
    Passed to the `run` method of each operation. Holds runtime information and utility functions.
    """

    directory: Path
    _read_func: LookupFunc
    _write_func: Callable[[str, DataValType], None]

    def exec_raw_cmd(self, cmd: list[str]) -> subprocess.CompletedProcess[str]:
        """
        Helper for shelling out. Removes falsy elements from `cmd` and doesn't throw for non-zero exit codes.

        Prefer using exec_cmd_with_result, since that wraps the result for you.
        """
        return subprocess.run(
            truthy_list(cmd),
            cwd=self.directory,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

    def exec_cmd(self, cmd: list[str]) -> OperationResult:
        """
        Shell out and run `cmd`, wrapping it in an `OperationResult` for better displaying.
        """
        result = self.exec_raw_cmd(cmd)
        return OperationResult.from_process(result, cmd=cmd)

    def read_data(self, key: str) -> DataValType:
        return self._read_func(key)

    def write_data(self, key: str, value: DataValType) -> None:
        self._write_func(key, value)


class CommonBase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ignored_fields_for_compare: ClassVar[set[str]] = set()
    """
    Which fields, if any, should be ignored when deciding whether two instances of an operation have diverged. Should include anything that doesn't affect the runtime behavior, like comments or labels.
    """

    @classmethod
    def __pydantic_on_complete__(cls, **kwargs):
        super().__pydantic_on_complete__(**kwargs)

        if unknown_fields := cls.ignored_fields_for_compare - cls.model_fields.keys():
            raise ValueError(
                f"{cls.__name__}: unknown ignored fields {sorted(unknown_fields)}"
            )

    def _compute_ignored_fields(self) -> dict[str, Any]:
        """
        Produce a dict of field names and subfield structures that should be excluded from a comparison.

        Each model can declare its own ignored_fields_for_compare.

        See: https://pydantic.dev/docs/validation/latest/concepts/serialization/#excluding-and-including-specific-fields
        """
        ignored_fields: dict[str, Any] = dict.fromkeys(
            self.ignored_fields_for_compare, True
        )
        for name, field in self:
            if name in ignored_fields:
                continue

            if isinstance(field, CommonBase):
                if subfields := field._compute_ignored_fields():
                    ignored_fields[name] = subfields

            elif isinstance(field, list):
                items = {
                    i: subfields
                    for i, item in enumerate(field)
                    if isinstance(item, CommonBase)
                    and (subfields := item._compute_ignored_fields())
                }
                if items:
                    ignored_fields[name] = items

        return ignored_fields

    def dump_for_comparison(self) -> dict[str, Any]:
        return self.model_dump(
            exclude_none=True,
            exclude=self._compute_ignored_fields(),
            serialize_as_any=True,
        )


# the text inside a `{{ }}` pair
TEMPLATE_REGEX = re.compile(r"\{\{\s*(\w+)\s*\}\}")


class BaseConfig(CommonBase):
    model_config = ConfigDict(use_attribute_docstrings=True)

    def _resolve(self, resolver: LookupFunc) -> Self:
        """
        (attempt to) materialize all templates into true values. Returns a copy of the original config.
        """

        def _resolve_str(s: str) -> str:
            return TEMPLATE_REGEX.sub(lambda m: str(resolver(m.group(1))), s)

        updates = {}
        for name, value in self:
            match value:
                case str(s):
                    updates[name] = _resolve_str(s)
                case list(l):
                    updates[name] = [
                        _resolve_str(s) if isinstance(s, str) else s for s in l
                    ]
                case dict(d):
                    updates[name] = {
                        k: _resolve_str(v) if isinstance(v, str) else v
                        for k, v in d.items()
                    }

        return self.model_copy(update=updates)


class BaseOperation(CommonBase):
    comment: Optional[str] = None
    directory_statuses: dict[AbsDirPath, Status] = {}

    always_rerun: ClassVar[bool] = False
    """
    Most operations are only run until they complete successfully, but operations can opt into re-running every time (e.g. to make assertions)
    """

    ignored_fields_for_compare: ClassVar[set[str]] = {"comment", "directory_statuses"}
    _resolved = False

    @final
    def run_and_record_result(
        self, raw_directory: Path, context: Context
    ) -> OperationResult:
        try:
            result = self.run(context)
        # Could get lots of errors here, but mostly I saw `FileNotFoundError` from subprocess.run()
        # when running non-existent commands
        except OSError as e:
            result = OperationResult(success=False, output=str(e))
        except NotImplementedError:
            result = OperationResult(
                success=False,
                output=f'Step "{self.summary}" does not implement `.run()`',
            )

        # internal to the plan, everything uses the plain, un-expanded directory
        self.record_result(raw_directory, result.success)
        return result

    # operation subclasses will implement this
    def run(self, context: Context) -> OperationResult:
        """
        The function that's called to actually execute the step. Probably runs a subcommand (preferably via `self.exec_cmd_with_result`).
        """
        raise NotImplementedError

    @property
    def summary(self) -> str:
        """
        A human-readable description of this step, used for disambiguating multiple steps of the same type (especially if they can be configured).

        Result string should probably include the underlying command, plus any important config values.
        """
        # children will provide this if needed
        return self.slug  # type: ignore

    # internal helpers
    def _resolve(self, resolver: LookupFunc) -> Self:
        """
        If this operation has a config, copy this operation and replace its config with a resolved copy.

        Otherwise, return the original untouched.
        """
        if config := cast("BaseConfig", getattr(self, CONFIG_KEY, None)):
            return self.model_copy(
                update={CONFIG_KEY: config._resolve(resolver), "_resolved": True},
                # we explicitly want to share other state between the copied instances of the model
                # for example, the directory_statuses of the copy that we run should be reflected in the original (which is owned by, and saved by, the Plan)
                deep=False,
            )

        return self

    # process controls
    @final
    def reset(self) -> None:
        self.directory_statuses = {}

    @final
    def is_completed(self, directory: Path) -> bool:
        return self.directory_statuses.get(directory) == "completed"

    @final
    def is_failed(self, directory: Path) -> bool:
        return self.directory_statuses.get(directory) == "failed"

    @final
    def is_pending(self, directory: Path) -> bool:
        return self.directory_statuses.get(directory, "not-started") == "not-started"

    @final
    def dir_status(self, directory: Path) -> Status:
        return self.directory_statuses.get(directory, "not-started")

    @final
    def initialize_dirs(self, directories: list[Path]) -> None:
        self.directory_statuses |= dict.fromkeys(directories, "not-started")

    @final
    def record_result(self, directory: Path, success: bool) -> None:
        self.directory_statuses[directory] = "completed" if success else "failed"

    # docs helpers
    @classmethod
    def to_markdown(cls) -> list[str]:
        """
        Returns a nicely formatted multiline markdown string that documents all of the properties on the model.
        """
        fields = cls.model_fields
        lines = [
            "",
            f"### {cls.__name__}",
            "",
            "\n".join(l.strip() for l in (cls.__doc__ or "").splitlines()),
            "",
            f"**Slug**: `{get_args(fields['slug'].annotation)[0]}`",
        ]

        if (raw_config := fields.get(CONFIG_KEY)) and raw_config.annotation:
            config = raw_config.annotation.model_fields

            lines += [
                "",
                f"#### Config{'' if raw_config.is_required() else ' (optional)'}",
                "",
                table_row("name", "type", "description", "default (if optional)"),
                table_row(*(["---"] * 4)),
                *[
                    table_row(
                        f"`{conf_key}`",
                        format_annotation(v.annotation),
                        v.description,
                        ""
                        if v.is_required()
                        else f"`{f'"{v.default}"' if isinstance(v.default, str) else v.default}`",
                    )
                    for conf_key, v in config.items()
                ],
            ]

        return lines

    @classmethod
    def to_markdown_summary(cls) -> tuple[str, str]:
        """
        Returns a tuple of (slug, required_config) to summarize this operation. The slug is also a link to the section in the docs.
        """

        fields = cls.model_fields

        config_note = "∅ None"
        if (raw_config := fields.get(CONFIG_KEY)) and (
            annotation := raw_config.annotation
        ):
            if any(f.is_required() for f in annotation.model_fields.values()):
                config_note = "✅ Reqiured"
            else:
                config_note = "☑️ Optional"

        return (
            f"[`{get_args(fields['slug'].annotation)[0]}`](#{cls.__name__})",
            config_note,
        )
