from contextlib import contextmanager
from contextvars import ContextVar

_request = ContextVar("auditoria_request", default=None)
_sistema = ContextVar("auditoria_sistema", default=False)


def fijar_request(request):
    return _request.set(request)


def soltar_request(token):
    _request.reset(token)


@contextmanager
def como_sistema():
    """Dentro de este bloque, los cambios se atribuyen a 'Sistema'."""
    token = _sistema.set(True)
    try:
        yield
    finally:
        _sistema.reset(token)


def quien():
    """(usuario, nombre) de quien está haciendo la petición actual."""
    if _sistema.get():
        return None, "Sistema"
    request = _request.get()
    usuario = getattr(request, "user", None)
    if usuario is not None and usuario.is_authenticated:
        return usuario, usuario.get_username()
    return None, "Sistema" if request is None else "Anónimo"
