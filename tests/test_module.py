import definitely


def test_get_version_short():
    # `mock.patch` wasn't cooperating here, so uh... yolo?
    old_version = definitely.__version__
    definitely.__version__ = (1, 2, 3, "alpha")

    try:
        assert definitely.get_version() == "1.2.3"
    finally:
        definitely.__version__ = old_version


def test_get_version_full():
    # `mock.patch` wasn't cooperating here, so uh... yolo?
    old_version = definitely.__version__
    definitely.__version__ = (1, 2, 3, "alpha", "omega")

    try:
        assert definitely.get_version(full=True) == "1.2.3-alpha-omega"
    finally:
        definitely.__version__ = old_version
