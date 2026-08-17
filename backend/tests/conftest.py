"""Configuración común de las pruebas.

El paquete `app` vive en `backend/src/`, que no está instalado en modo editable,
así que cada módulo de test tendría que manipular `sys.path` por su cuenta. Se
hace una sola vez aquí.
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
