def truthy_list[T](l: list[T]) -> list[T]:
    """
    Return a list with the falsy elements removed
    """
    return list(filter(None, l))
