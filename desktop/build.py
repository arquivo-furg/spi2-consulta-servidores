"""Execute no sistema de destino: python desktop/build.py."""

import importlib
import platform
from pathlib import Path
import subprocess
import sys


def check_tkinter():
    # Sem Tk instalado, o PyInstaller pode gerar um arquivo que falha só ao abrir.
    # Tcl() verifica a biblioteca sem exigir monitor na máquina de compilação.
    try:
        tkinter = importlib.import_module('tkinter')
        tkinter.Tcl().eval('info patchlevel')
    except Exception as error:
        raise SystemExit(
            'Tkinter/Tcl não está disponível neste Python. '
            'Ubuntu/Debian: sudo apt install python3-tk. '
            'Fedora: sudo dnf install python3-tkinter. '
            'Windows: habilite Tcl/Tk na instalação do Python. '
            'Depois recrie o venv se necessário e compile novamente. '
            f'Detalhe: {error}'
        ) from None


def main():
    root = Path(__file__).resolve().parent.parent
    target = platform.system().lower()
    if target not in ('windows', 'linux'):
        raise SystemExit('Compile em Windows ou Linux, no próprio sistema de destino.')
    check_tkinter()
    output = root / 'output' / 'desktop' / target
    # PyInstaller gera para o sistema onde está rodando; repetir o build em cada SO.
    # onefile reúne o cliente em um executável, sem embutir a API ou o banco.
    subprocess.run([
        sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
        '--onefile', '--windowed', '--name', 'ConsultaServidores',
        '--distpath', str(output), '--workpath', str(output / 'build'),
        '--specpath', str(output), str(root / 'desktop' / 'app.py'),
    ], cwd=root, check=True)
    print(f'Executável gerado em {output}')


if __name__ == '__main__':
    main()
