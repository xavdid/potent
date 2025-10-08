def truthy_list[T](l: list[T]) -> list[T]:
    """
    Return a list with the falsy elements removed
    """
    return list(filter(None, l))


def indent_command_output(output: bytes, indent=3) -> str:
    """
    print the output of a shell command indented to match surrounding lines
    """
    lines = output.decode().splitlines()
    return "\n".join([f"{' ' * indent}{l}" for l in lines])
