"""Genera requirements.lock.txt a partir del .venv que se usa en desarrollo.

Excluye el propio proyecto (lo instala el Dockerfile) y las herramientas que
solo se usan para generar assets: fonttools/brotli (subconjunto woff2) y
pillow (comparacion de capturas). Ninguna aparece en los imports de la app.
"""
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(r"C:\Users\USER\Desktop\Swing_Trading_consultor_ia")
PY = ROOT / ".venv" / "Scripts" / "python.exe"

EXCLUIR = {
    "swing-trading-consultor-ia",  # el propio proyecto
    "fonttools",                    # build: subconjunto de fuentes
    "brotli",                       # build: compresion woff2
    "pillow",                       # build: comparacion de capturas
    "pip",
    "setuptools",
    "wheel",
}

salida = subprocess.run(
    [str(PY), "-m", "pip", "list", "--format=freeze"],
    capture_output=True,
    text=True,
    check=True,
).stdout

lineas = []
for ln in salida.splitlines():
    ln = ln.strip()
    if not ln or "==" not in ln:
        continue
    nombre = ln.split("==", 1)[0]
    if nombre.lower() in EXCLUIR:
        continue
    lineas.append(ln)

cabecera = (
    "# Dependencias de runtime congeladas del entorno que se uso en desarrollo.\n"
    "# Generado con: python -m pip list --format=freeze  (ver tools/gen_lock.py)\n"
    "# Excluye el propio proyecto y fonttools/brotli/pillow, que solo se usan\n"
    "# para generar assets. Python 3.12.\n"
)

destino = ROOT / "requirements.lock.txt"
destino.write_text(cabecera + "\n".join(sorted(lineas, key=str.lower)) + "\n", encoding="utf-8")

print("requirements.lock.txt:", len(lineas), "paquetes")
print("excluidos:", ", ".join(sorted(EXCLUIR)))
