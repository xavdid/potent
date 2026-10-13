from importlib.metadata import EntryPoint, entry_points

from potent.operations._base import BaseOperation


def validate_plugin(
    ep: EntryPoint,
) -> tuple[list[type[BaseOperation]], list[str]]:
    """
    Returns the loaded operations or as many issues as we can surface about them
    """

    ops = ep.load()
    package_name = ep.dist.name if ep.dist else "unknown-package"
    ident = f"{package_name}.{ep.name}{'' if ep.dist else f' ({ep.value})'}"

    if not isinstance(ops, list):
        return [], [f"Plugins must be lists, but {ident} is a {type(ops)}"]

    errors = []

    for idx, op in enumerate(ops):
        if not issubclass(op, BaseOperation):
            errors.append(
                f"{ident}: item at index {idx} is not a child of BaseOperation"
            )
            continue

        if not (slug_field := op.model_fields.get("slug")):
            errors.append(f'{ident}: {op} has no "slug" field')
            continue

        if not isinstance(slug_field.default, str):
            errors.append(f"{ident}: {op}.slug does not have a default value")
            continue

        if not slug_field.default.startswith(f"{package_name}."):
            errors.append(f'{ident}: {op}.slug should start with "{package_name}."')
            continue

    return ops, errors


def get_ops_from_plugins() -> list[type[BaseOperation]]:
    loaded_ops: list[type[BaseOperation]] = []
    errors: list[str] = []

    for entry_point in entry_points(group="potent"):
        ops, errs = validate_plugin(entry_point)
        if errs:
            errors.extend(errs)
        else:
            loaded_ops.extend(ops)

    if errors:
        for e in errors:
            print(f"  {e}")
        raise RuntimeError("There were errors loading plugins, see above")

    return loaded_ops
