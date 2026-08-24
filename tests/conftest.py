"""
Configuracion compartida de pytest.

Este archivo lo carga pytest solo. No hay que importarlo.
"""

import sys
from pathlib import Path

import pytest

# Permite "from cubomatica import ..." sin instalar el paquete
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture
def api():
    """Una instancia limpia de la API para cada test."""
    from cubomatica.api import Api

    return Api()


@pytest.fixture
def web_dir() -> Path:
    """Carpeta donde vive la web."""
    return ROOT / "src" / "cubomatica" / "web"
