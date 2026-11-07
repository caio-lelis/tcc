"""Erros dos relatórios, cada um com o código HTTP que a API devolve."""


class ErroRelatorio(Exception):
    status = 400

    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


class ErroNaoEncontrado(ErroRelatorio):
    status = 404


class ErroConflito(ErroRelatorio):
    status = 409


class ErroEntrada(ErroRelatorio):
    status = 422


class ErroIndisponivel(ErroRelatorio):
    status = 503
