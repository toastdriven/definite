import definite


def test_get_version_short():
    # `mock.patch` wasn't cooperating here, so uh... yolo?
    old_version = definite.__version__
    definite.__version__ = (1, 2, 3, "alpha")

    try:
        assert definite.get_version() == "1.2.3"
    finally:
        definite.__version__ = old_version


def test_get_version_full():
    # `mock.patch` wasn't cooperating here, so uh... yolo?
    old_version = definite.__version__
    definite.__version__ = (1, 2, 3, "alpha", "omega")

    try:
        assert definite.get_version(full=True) == "1.2.3-alpha-omega"
    finally:
        definite.__version__ = old_version
