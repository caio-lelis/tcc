"""Regra de acerto (Seção 4.6.3): o resultado obtido é equivalente ao do gabarito?

Equivalente quando:
  (i)   tem o mesmo conjunto de linhas, sem considerar a ordem, exceto quando a
        pergunta pede ordenação;
  (ii)  nomes e ordem das colunas não importam;
  (iii) diferenças numéricas de até 0,01 são aceitas (arredondamento).

A comparação é automática e determinística. O que ela não decide sozinha vira
"limítrofe": o veredito automático continua valendo, mas a execução é marcada
para revisão manual, com a justificativa registrada (Seção 4.6.3).
"""
from typing import Any, NamedTuple

TOLERANCIA = 0.01
_FOLGA = 1e-9  # erro de ponto flutuante: 0.30 - 0.29 não pode reprovar por 1e-17
_MAX_PERMUTACOES = 5040  # 7 colunas ambíguas entre si; acima disso, desiste e marca limítrofe


class Comparacao(NamedTuple):
    igual: bool
    limitrofe: str | None = None  # motivo para revisão manual, se houver


def _numero(valor: Any) -> bool:
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def valores_iguais(a: Any, b: Any) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if _numero(a) and _numero(b):
        return abs(a - b) <= TOLERANCIA + _FOLGA
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a == b
    return a == b


def _linhas_iguais(a: list[Any], b: list[Any]) -> bool:
    return all(valores_iguais(x, y) for x, y in zip(a, b))


def _chave(valor: Any) -> tuple:
    """Ordena valores de tipos diferentes sem erro: nulos, booleanos, números, textos."""
    if valor is None:
        return (0, 0)
    if isinstance(valor, bool):
        return (1, valor)
    if _numero(valor):
        return (2, valor)
    return (3, str(valor))


def _mesmo_conjunto(esperado: list[list[Any]], obtido: list[list[Any]]) -> bool:
    """Mesmas linhas, em qualquer ordem (com repetições: é um multiconjunto)."""
    chave_linha = lambda linha: [_chave(v) for v in linha]  # noqa: E731
    a, b = sorted(esperado, key=chave_linha), sorted(obtido, key=chave_linha)
    if all(_linhas_iguais(x, y) for x, y in zip(a, b)):
        return True
    # A tolerância pode embaralhar a ordenação (1,004 e 1,006): casa linha a linha.
    livres = list(b)
    for linha in a:
        for i, candidata in enumerate(livres):
            if _linhas_iguais(linha, candidata):
                del livres[i]
                break
        else:
            return False
    return True


def _colunas_compativeis(esperado: list[list[Any]], obtido: list[list[Any]], n: int) -> list[list[int]]:
    """Para cada coluna do gabarito, as colunas do resultado com os mesmos valores."""
    def coluna(linhas, i):
        return sorted((linha[i] for linha in linhas), key=_chave)

    do_obtido = [coluna(obtido, j) for j in range(n)]
    candidatas = []
    for i in range(n):
        alvo = coluna(esperado, i)
        candidatas.append([j for j in range(n) if all(valores_iguais(x, y) for x, y in zip(alvo, do_obtido[j]))])
    return candidatas


def _contem_colunas(esperado: list[list[Any]], obtido: list[list[Any]]) -> bool:
    """O resultado traz todas as colunas do gabarito e mais algumas?"""
    n = len(esperado[0])
    for i in range(n):
        alvo = sorted((linha[i] for linha in esperado), key=_chave)
        if not any(
            all(valores_iguais(x, y) for x, y in zip(alvo, sorted((linha[j] for linha in obtido), key=_chave)))
            for j in range(len(obtido[0]))
        ):
            return False
    return True


def comparar(esperado: list[list[Any]], obtido: list[list[Any]], ordenada: bool = False,
             truncado: bool = False) -> Comparacao:
    """Compara as linhas do gabarito com as do resultado obtido."""
    if truncado:
        return Comparacao(False, "resultado cortado no limite de linhas (RNF04)")
    if len(esperado) != len(obtido):
        return Comparacao(False)
    if not esperado:
        return Comparacao(True)

    n = len(esperado[0])
    largura = len(obtido[0])
    if largura != n:
        if largura > n and _contem_colunas(esperado, obtido):
            return Comparacao(False, f"traz as {n} coluna(s) do gabarito e mais {largura - n}")
        return Comparacao(False)

    candidatas = _colunas_compativeis(esperado, obtido, n)
    if any(not c for c in candidatas):
        return Comparacao(False)

    total = 1
    for c in candidatas:
        total *= len(c)
    if total > _MAX_PERMUTACOES:
        return Comparacao(False, "muitas colunas com os mesmos valores: comparar manualmente")

    def tentar(i: int, usadas: tuple[int, ...]):
        if i == n:
            yield usadas
            return
        for j in candidatas[i]:
            if j not in usadas:
                yield from tentar(i + 1, usadas + (j,))

    ordem_errada = False
    for ordem in tentar(0, ()):
        reordenado = [[linha[j] for j in ordem] for linha in obtido]
        if ordenada:
            if all(_linhas_iguais(x, y) for x, y in zip(esperado, reordenado)):
                return Comparacao(True)
            ordem_errada = ordem_errada or _mesmo_conjunto(esperado, reordenado)
        elif _mesmo_conjunto(esperado, reordenado):
            return Comparacao(True)

    if ordem_errada:
        return Comparacao(False, "mesmas linhas do gabarito, em outra ordem")
    return Comparacao(False)
