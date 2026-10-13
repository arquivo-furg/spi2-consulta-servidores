"""Execute no sistema de destino: python desktop/build.py."""

import platform
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parent.parent
    target = platform.system().lower()
    if target not in ('windows', 'linux'):
        raise SystemExit('Compile em Windows ou Linux, no próprio sistema de destino.')
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
