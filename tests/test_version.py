import agyloop


def test_version_is_string() -> None:
    assert isinstance(agyloop.__version__, str)
