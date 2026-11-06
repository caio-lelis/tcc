"""Gera o modelo de partida: 4 tabelas fictícias do domínio comercial.

Os dados são inventados (sem LGPD) e servem para desenvolver e testar o
Data Talk antes de haver uma empresa parceira. A semente é fixa, então
os CSVs saem sempre iguais.

As tabelas têm de propósito as "armadilhas" descritas em README.md:
códigos internos (resolvidos pelo C1) e regras de negócio (resolvidas pelo C2).

Uso:  python gerar_exemplo.py
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEMENTE = 2026
INICIO = date(2026, 1, 1)
FIM = date(2026, 10, 31)  # "hoje" no cenário fictício
PASTA = Path(__file__).parent

rng = random.Random(SEMENTE)

PRIMEIROS = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Fábio", "Gabriela", "Heitor",
             "Isabela", "João", "Karina", "Lucas", "Marina", "Nicolas", "Olívia", "Pedro",
             "Rafaela", "Samuel", "Talita", "Vinícius"]
SOBRENOMES = ["Almeida", "Barros", "Cardoso", "Duarte", "Esteves", "Freitas", "Gomes",
              "Hora", "Lacerda", "Moraes", "Nogueira", "Pacheco", "Queiroz", "Rezende",
              "Siqueira", "Teles", "Vieira"]
SUFIXOS_EMPRESA = ["Comércio", "Serviços", "Tecnologia", "Distribuidora", "Consultoria",
                   "Indústria", "Clínica", "Escola", "Logística"]
UFS = ["DF"] * 5 + ["SP"] * 4 + ["GO"] * 3 + ["MG"] * 2 + ["RJ", "BA", "PR"]
SEGMENTOS = ["Varejo", "Serviços", "Indústria", "Saúde", "Educação"]


def dia_aleatorio(inicio: date, fim: date) -> date:
    return inicio + timedelta(days=rng.randint(0, (fim - inicio).days))


def gravar(nome: str, linhas: list[dict]) -> None:
    caminho = PASTA / f"{nome}.csv"
    with caminho.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(linhas[0]))
        escritor.writeheader()
        for linha in linhas:
            escritor.writerow({k: "" if v is None else v for k, v in linha.items()})
    print(f"{caminho.name}: {len(linhas)} linhas")


def gerar_vendedores() -> list[dict]:
    nomes = rng.sample([f"{p} {s}" for p in PRIMEIROS for s in SOBRENOMES], 8)
    equipes = ["SDR"] * 3 + ["CLOSER"] * 5
    vendedores = [
        {"id": i + 1, "nome": nome, "equipe": equipe, "ativo": "true"}
        for i, (nome, equipe) in enumerate(zip(nomes, equipes))
    ]
    vendedores[-1]["ativo"] = "false"  # um closer saiu da empresa em junho
    return vendedores


def gerar_clientes(n: int = 80) -> list[dict]:
    clientes = []
    for i in range(n):
        nome = f"{rng.choice(SOBRENOMES)} {rng.choice(SUFIXOS_EMPRESA)}"
        clientes.append({
            "id": i + 1,
            "nome": nome,
            "uf": rng.choice(UFS),
            "segmento": rng.choice(SEGMENTOS),
            "data_cadastro": dia_aleatorio(date(2025, 6, 1), date(2026, 9, 30)).isoformat(),
        })
    return clientes


def gerar_reunioes(clientes, vendedores, n: int = 400) -> list[dict]:
    sdrs = [v["id"] for v in vendedores if v["equipe"] == "SDR"]
    closers_ativos = [v["id"] for v in vendedores if v["equipe"] == "CLOSER" and v["ativo"] == "true"]
    closer_inativo = next(v["id"] for v in vendedores if v["ativo"] == "false")

    reunioes = []
    for i in range(n):
        data_reuniao = dia_aleatorio(INICIO, FIM)
        # o closer inativo só atendeu até junho
        closers = closers_ativos + ([closer_inativo] if data_reuniao < date(2026, 7, 1) else [])
        reunioes.append({
            "id": i + 1,
            "cliente_id": rng.choice(clientes)["id"],
            "sdr_id": rng.choice(sdrs),
            "closer_id": rng.choice(closers),
            "data_reuniao": data_reuniao.isoformat(),
            # R = realizada, N = não compareceu (no-show), M = remarcada
            "situacao": rng.choices(["R", "N", "M"], weights=[70, 18, 12])[0],
            # 1A = primeira reunião, RET = retorno
            "tipo": rng.choices(["1A", "RET"], weights=[75, 25])[0],
        })
    return reunioes


def gerar_contratos(reunioes) -> list[dict]:
    realizadas = [r for r in reunioes if r["situacao"] == "R"]
    contratos = []
    for r in realizadas:
        if rng.random() > 0.85:  # nem toda reunião realizada gera contrato
            continue
        criacao = date.fromisoformat(r["data_reuniao"]) + timedelta(days=rng.randint(0, 5))
        if criacao > FIM:
            continue
        valor = rng.randrange(1500, 15001, 50)
        desconto = 0 if rng.random() < 0.6 else round(valor * rng.choice([0.05, 0.10, 0.15, 0.20]), 2)

        status, assinatura, cancelamento = "E", None, None  # E = enviado, aguardando assinatura
        destino = rng.choices(["assina", "cancela_antes", "espera"], weights=[72, 10, 18])[0]
        if destino == "assina":
            # pode cair no mês seguinte ao da criação (armadilha da data)
            dia = criacao + timedelta(days=rng.randint(0, 20))
            if dia <= FIM:
                status, assinatura = "A", dia  # A = assinado
                if rng.random() < 0.15:  # cancelado depois de assinar
                    canc = dia + timedelta(days=rng.randint(1, 30))
                    if canc <= FIM:
                        status, cancelamento = "C", canc  # C = cancelado
        elif destino == "cancela_antes":
            canc = criacao + timedelta(days=rng.randint(1, 15))
            if canc <= FIM:
                status, cancelamento = "C", canc

        contratos.append({
            "id": len(contratos) + 1,
            "cliente_id": r["cliente_id"],
            "vendedor_id": r["closer_id"],  # quem fecha é o closer
            "valor": f"{valor:.2f}",
            "desconto": f"{desconto:.2f}",
            "status": status,
            "data_criacao": criacao.isoformat(),
            "data_assinatura": assinatura.isoformat() if assinatura else None,
            "data_cancelamento": cancelamento.isoformat() if cancelamento else None,
        })
    return contratos


if __name__ == "__main__":
    vendedores = gerar_vendedores()
    clientes = gerar_clientes()
    reunioes = gerar_reunioes(clientes, vendedores)
    contratos = gerar_contratos(reunioes)
    for nome, linhas in [("vendedores", vendedores), ("clientes", clientes),
                         ("reunioes", reunioes), ("contratos", contratos)]:
        gravar(nome, linhas)
