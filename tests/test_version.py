import re

import opensincera


def test_version_is_a_non_empty_pep440_string() -> None:
    assert isinstance(opensincera.__version__, str)
    assert opensincera.__version__
    assert re.match(r"^\d+\.\d+\.\d+", opensincera.__version__)
