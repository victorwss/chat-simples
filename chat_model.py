import dataclasses, json
from typing import Any, Sequence
from dataclasses import dataclass
from datetime import datetime

# Obtido de https://stackoverflow.com/a/51286749/540552
class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)

@dataclass(frozen = True)
class Timestamp:
    ano: int
    mes: int
    dia: int
    hora: int
    minuto: int
    segundo: int

    @staticmethod
    def now() -> "Timestamp":
        d = datetime.now()
        return Timestamp(d.year, d.month, d.day, d.hour, d.minute, d.second)

    @property
    def formatado(self) -> str:
        return f"{self.dia}/{self.mes}/{self.ano} {self.hora}:{self.minuto}:{self.segundo}"

@dataclass(frozen = True)
class InformacoesUsuarioSemSenha:
    login: str
    nome: str

@dataclass(frozen = True)
class InformacoesUsuarioComSenha:
    login: str
    nome: str
    senha: str

    @property
    def sem_senha(self) -> InformacoesUsuarioSemSenha:
        return InformacoesUsuarioSemSenha(self.login, self.nome)

class UsuarioJaExiste(Exception):
    pass

class SenhaIncorreta(Exception):
    pass

@dataclass(frozen = True)
class Mensagem:
    autor: InformacoesUsuarioSemSenha
    texto: str
    msg_id: int
    hora: Timestamp

    @staticmethod
    def new(autor: InformacoesUsuarioSemSenha, texto: str, msg_id: int) -> "Mensagem":
        return Mensagem(autor, texto, msg_id, Timestamp.now())

@dataclass(frozen = True)
class ListaMensagens:
    mensagens: Sequence[Mensagem]

    @property
    def json(self) -> str:
        return json.dumps(self, cls = EnhancedJSONEncoder)

class ChatRoom:
    def __init__(self, nome: str, chat_id: int) -> None:
        self.__nome = nome
        self.__chat_id = chat_id
        self.__mensagens: list[Mensagem] = []

    @property
    def nome(self) -> str:
        return self.__nome

    @property
    def chat_id(self) -> int:
        return self.__chat_id

    def desde(self, msg_id: int) -> ListaMensagens:
        if msg_id <= 0: raise ValueError
        if len(self.__mensagens) == 0: return ListaMensagens([])
        return ListaMensagens(self.__mensagens[msg_id - 1:])

    def postar(self, autor: InformacoesUsuarioSemSenha, texto: str) -> Mensagem:
        m = Mensagem.new(autor, texto, len(self.__mensagens) + 1)
        self.__mensagens.append(m)
        return m

class ChatArea:
    def __init__(self) -> None:
        self.__chats: dict[int, ChatRoom] = {}

    def novo_chat(self, nome: str) -> int:
        chat_id = len(self.__chats) + 1
        self.__chats[chat_id] = ChatRoom(nome, chat_id)
        return chat_id

    def sala(self, chat_id: int) -> ChatRoom | None:
        if chat_id not in self.__chats: return None
        return self.__chats[chat_id]

    def listar(self) -> list[ChatRoom]:
        return list(self.__chats.values())

class DbUsuarios:
    def __init__(self) -> None:
        self.__usuarios_por_login: dict[str, InformacoesUsuarioComSenha] = {}

    def novo_usuario(self, login: str, nome: str, senha: str) -> None:
        if login in self.__usuarios_por_login: raise UsuarioJaExiste
        u = InformacoesUsuarioComSenha(login, nome, senha)
        self.__usuarios_por_login[login] = u

    def validar_login(self, login: str, senha: str) -> InformacoesUsuarioSemSenha:
        if login not in self.__usuarios_por_login: raise SenhaIncorreta
        u = self.__usuarios_por_login[login]
        if u.senha != senha: raise SenhaIncorreta
        return u.sem_senha

    def revalidar(self, login: str) -> InformacoesUsuarioSemSenha | None:
        if login not in self.__usuarios_por_login: return None
        return self.__usuarios_por_login[login].sem_senha