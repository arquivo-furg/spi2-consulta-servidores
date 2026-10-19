# Cliente desktop

Interface Python/Tkinter que consulta a mesma API da versão web por HTTP/HTTPS.
Não acessa o banco diretamente. Oferece busca exata ou por similaridade de nome,
cargo, UF, órgão, filtros combinados, limite da similaridade e páginas de 10 resultados.

## Executar

Inicie a API e o banco conforme o README da raiz. O frontend não é necessário
para usar o desktop. Importe os dados públicos para obter resultados.

Nos pacotes compilados, abra `ConsultaServidores.exe` no Windows ou
`ConsultaServidores` no Linux. Não é necessário instalar Python ou Docker
na máquina do cliente. No Linux, use uma sessão gráfica com X11 ou XWayland;
caso necessário, dê permissão com `chmod +x ConsultaServidores`.

O endereço padrão é `http://localhost:8000`. Pode ser alterado na janela ou
pela opção `--api-url http://endereco:8000`. A API precisa estar acessível.
Em outra máquina, `localhost` é a própria máquina do cliente, não o servidor.

Para executar pelo código, use Python 3.10 ou superior com Tkinter instalado:

```bash
python desktop/app.py
```

O Tkinter é um componente opcional da instalação do Python, não um pacote para
adicionar com `pip install tkinter`. O venv usa esse componente do Python que o criou:

- Ubuntu/Debian: `sudo apt install python3-tk`.
- Fedora: `sudo dnf install python3-tkinter`.
- Windows: no instalador do Python, habilite a opção Tcl/Tk e IDLE.

Depois de instalar, confira `python -m tkinter`: deve abrir uma janela de teste.
Se o venv foi criado com outro Python, recrie-o com o interpretador correto.
A execução pelo código usa somente a biblioteca padrão do Python.

## Compilar

Instale primeiro o Tkinter conforme o sistema acima. Depois crie um ambiente
virtual e instale a dependência de compilação:

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux: source .venv/bin/activate
python -m pip install -r desktop/requirements-build.txt
python -m tkinter
python desktop/build.py
```

Compile separadamente em cada sistema: Windows produz `.exe`; Linux produz
um binário ELF, em `output/desktop/windows/` e `output/desktop/linux/`.
A compilação Linux requer Tkinter, `binutils` e a biblioteca compartilhada
do Python instalados no sistema (no Ubuntu 22.04: `python3-tk binutils libpython3.10`).
O PyInstaller inclui Python e Tcl/Tk no executável, mas não a API nem os dados.
Não há compilação cruzada. Os arquivos gerados não fazem parte do código versionado.
O build verifica Tkinter/Tcl antes de chamar o PyInstaller e para se o componente
estiver ausente ou quebrado. `output/` é ignorada pelo Git em qualquer clone.

Se um executável pronto pedir o módulo `tkinter`, ele foi empacotado sem esse
componente: corrija o ambiente de compilação e gere outro pacote. Instalar
Tkinter no computador de quem recebe não corrige o conteúdo de um binário incompleto.

Os pacotes desta entrega são x86_64: Windows 10 e Linux compilado em Ubuntu
22.04 (glibc 2.35). A verificação Linux usa Xvfb, sem sessão Wayland real.
Outras distribuições, versões de glibc e máquinas ARM não foram validadas.

## Testes

```bash
python -m unittest discover -s desktop/tests -v
```

Os testes de interface exigem uma sessão gráfica. Em Linux sem monitor,
podem ser executados com `xvfb-run -a python -m unittest discover -s desktop/tests -v`.
