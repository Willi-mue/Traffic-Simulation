import os

import pytest

from traffic_sim import i18n

# Qt tests run without a visible window (also on CI servers without a display).
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(autouse=True)
def default_language():
    """Every test starts in the default language, even if a previous test switched it."""
    i18n.set_language(i18n.DEFAULT_LANGUAGE)
    yield
    i18n.set_language(i18n.DEFAULT_LANGUAGE)
