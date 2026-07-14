"""Fixtures comuni. Tutti i test sono hermetic: brain in directory temporanee."""

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture()
def store(tmp_path):
    """MemoryStore fresco su una dir temporanea (un brain nuovo per ogni test)."""
    from wadachi.store import MemoryStore
    return MemoryStore(str(tmp_path / "brain"))


@pytest.fixture(scope="session")
def srv(tmp_path_factory):
    """Il modulo server importato UNA volta con BRAIN_DIR temporaneo di sessione.

    I tool sono funzioni module-level che condividono store/search singleton,
    quindi i test sui tool condividono lo stesso brain di sessione.
    """
    os.environ["BRAIN_DIR"] = str(tmp_path_factory.mktemp("server-brain"))
    import wadachi.server as server
    return server
