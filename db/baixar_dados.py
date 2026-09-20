"""Baixa os arquivos do período usado no projeto a partir dos links abaixo."""
from pathlib import Path
from urllib.request import urlretrieve


APOSENTADOS = [
    "http://repositorio.dados.gov.br/segrt/APOSENTADOS_092025.csv",
    "http://repositorio.dados.gov.br/segrt/APOSENTADOS_102025.csv",
    "http://repositorio.dados.gov.br/segrt/APOSENTADOS_112025.csv",
    "http://repositorio.dados.gov.br/segrt/APOSENTADOS_122025.csv",
    "http://repositorio.dados.gov.br/segrt/Aposentados/2026/APOSENTADOS_012026.csv",
    "http://repositorio.dados.gov.br/segrt/Aposentados/2026/APOSENTADOS_022026.csv",
    "http://repositorio.dados.gov.br/segrt/Aposentados/2026/APOSENTADOS_032026.csv",
    "http://repositorio.dados.gov.br/segrt/Aposentados/2026/APOSENTADOS_042026.csv",
    "http://repositorio.dados.gov.br/segrt/Aposentados/2026/APOSENTADOS_052026.csv",
    "http://repositorio.dados.gov.br/segrt/Aposentados/2026/APOSENTADOS_062026.csv",
    "http://repositorio.dados.gov.br/segrt/Aposentados/2026/APOSENTADOS_072026.csv",
]

CARREIRAS = [
    "http://repositorio.dados.gov.br/segrt/CARREIRA_092025.txt",
    "http://repositorio.dados.gov.br/segrt/CARREIRA_102025.txt",
    "http://repositorio.dados.gov.br/segrt/CARREIRA_112025.txt",
    "http://repositorio.dados.gov.br/segrt/CARREIRA_122025.txt",
    "http://repositorio.dados.gov.br/segrt/Cargos%20e%20Carreiras/2026/CARREIRA_012026.txt",
    "http://repositorio.dados.gov.br/segrt/Cargos%20e%20Carreiras/2026/CARREIRA_022026.txt",
    "http://repositorio.dados.gov.br/segrt/Cargos%20e%20Carreiras/2026/CARREIRA_032026.txt",
    "http://repositorio.dados.gov.br/segrt/Cargos%20e%20Carreiras/2026/CARREIRA_042026.txt",
    "http://repositorio.dados.gov.br/segrt/Cargos%20e%20Carreiras/2026/CARREIRA_052026.txt",
    "http://repositorio.dados.gov.br/segrt/Cargos%20e%20Carreiras/2026/CARREIRA_062026.txt",
    "http://repositorio.dados.gov.br/segrt/Cargos%20e%20Carreiras/2026/CARREIRA_072026.txt",
]


def baixar_dados(destino: Path) -> None:
    for pasta, links in [("aposentados", APOSENTADOS), ("carreiras", CARREIRAS)]:
        folder = destino / pasta
        folder.mkdir(parents=True, exist_ok=True)
        for link in links:
            arquivo = folder / link.rsplit("/", 1)[1]
            if arquivo.exists():
                print(f"Já existe: {arquivo.name}")
                continue
            print(f"Baixando {arquivo.name}...", flush=True)
            # Um download interrompido não pode ser confundido com o arquivo completo.
            parcial = arquivo.with_suffix(arquivo.suffix + ".part")
            urlretrieve(link, parcial)
            parcial.replace(arquivo)


if __name__ == "__main__":
    baixar_dados(Path(__file__).resolve().parents[1] / "dados")
