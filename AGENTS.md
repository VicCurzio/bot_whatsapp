# AGENTS.md

## Estilo de trabajo

Priorizá el bajo consumo de tokens. Hacé el cambio pedido y nada más — no corras
tests, no levantes el server, no verifiques en browser salvo que se pida
explícitamente. Eso lo prueba el mantenedor.

Nunca uses emojis (ni en código, comentarios, notas o commits). No agregues
líneas de co-autoría en los commits.

## Estándares del repo

Piso mínimo y entrega:

- README de cinco minutos, `.env.example` con
  validación al arrancar, verificación automática antes de que el código entre,
  logs útiles, fechas en UTC.
- Conventional Commits, versión
  semántica con etiqueta de git, `CHANGELOG.md` escrito para quien lo usa.

Traducido a Python: `pyproject.toml` con versiones fijas hace de
`.env.example` (es lo que vuelve reproducible la instalación), y el registro de
tanda de `envios_log.py` hace de identificador de pedido: sin él, una tanda
cortada a la mitad no se puede reconstruir.
