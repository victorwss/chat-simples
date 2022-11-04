from typing import Any, Callable, cast
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.wrappers.response import Response
import dataclasses
from chat_model import *

usuarios = DbUsuarios()
chats = ChatArea()

app = Flask(__name__)
app.secret_key = "senha super secreta que você nunca deve compartilhar com ninguém"
app.config["SESSION_TYPE"] = "filesystem"

# Telas de login e criar usuário.

@app.route("/login")
def tela_login() -> str:
    mensagem = request.args.get("mensagem", "")
    erro = request.args.get("erro", "")
    return render_template("login.html", mensagem = mensagem, erro = erro)

@app.route("/usuario/novo")
def tela_novo_user() -> str:
    mensagem = request.args.get("mensagem", "")
    erro = request.args.get("erro", "")
    return render_template("novo_user.html", mensagem = mensagem, erro = erro)

@app.route("/login", methods = ["POST"])
def login() -> Response:
    logar(None)
    login_usuario = request.form.get("login", "")
    senha_usuario = request.form.get("senha", "")
    try:
        logar(usuarios.validar_login(login_usuario, senha_usuario))
        return redirect_menu_html()
    except SenhaIncorreta as erro:
        return redirect_login_html(erro = "Senha errada.")

@app.route("/usuario/novo", methods = ["POST"])
def novo_user() -> Response:
    logar(None)
    login_usuario = request.form.get("login", "")
    nome_usuario = request.form.get("nome", "")
    senha_usuario = request.form.get("senha", "")
    senha_usuario2 = request.form.get("senha2", "")
    if senha_usuario != senha_usuario2:
        return redirect_criar_usuario_html(erro = "As senhas não coincidem.")
    try:
        usuarios.novo_usuario(login_usuario, nome_usuario, senha_usuario)
        return redirect_login_html(mensagem = "Usuário criado. Faça o login.")
    except UsuarioJaExiste as erro:
        return redirect_criar_usuario_html(erro = f"O usuário com o login {login_usuario} já existe.")

@app.route("/logout", methods = ["POST"])
def logout() -> Response:
    logar(None)
    return redirect_login_html(mensagem = "Tchau.")

def redirect_menu_html(mensagem: str = None, erro: str = None) -> Response:
    u = url_for("menu")
    if mensagem: u += "?mensagem=" + mensagem
    if erro: u += "?erro=" + erro
    return redirect(u)

def redirect_login_html(mensagem: str = None, erro: str = None) -> Response:
    u = url_for("tela_login")
    if mensagem: u += "?mensagem=" + mensagem
    if erro: u += "?erro=" + erro
    return redirect(u)

def redirect_criar_usuario_html(mensagem: str = None, erro: str = None) -> Response:
    u = url_for("tela_novo_user")
    if mensagem: u += "?mensagem=" + mensagem
    if erro: u += "?erro=" + erro
    return redirect(u)

# Controla o login na sessão.

def quem_esta_logado() -> InformacoesUsuarioSemSenha | None:
    if "usuario_logado" not in session: return None
    login = cast(str, session["usuario_logado"])
    logado = usuarios.revalidar(login)
    logar(logado)
    return logado

def logar(usuario: InformacoesUsuarioSemSenha | None) -> None:
    if usuario is not None:
        session["usuario_logado"] = usuario.login
    elif "usuario_logado" in session:
        del session["usuario_logado"]

def apenas_usuarios_logados(wrapped: Callable[..., Any]) -> Callable[..., Any]:
    from functools import wraps

    @wraps(wrapped)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if quem_esta_logado() is None:
            return redirect(url_for("tela_login"))
        return wrapped(*args, **kwargs)
    return wrapper

# Áreas para usuários logados contendo a funcionalidade do chat.

@app.route("/")
@apenas_usuarios_logados
def menu() -> str:
    salas = chats.listar()
    return render_template("menu.html", salas = salas, usuario_logado = quem_esta_logado())

@app.route("/chat/novo", methods = ["POST"])
@apenas_usuarios_logados
def new_chat() -> Response:
    nome_chat = request.form["nome"]
    chat_id = chats.novo_chat(nome_chat)
    return redirect(url_for("chat_html", chat_id = chat_id))

@app.route("/chat/<int:chat_id>/html")
@apenas_usuarios_logados
def chat_html(chat_id: int) -> str | tuple[str, int]:
    sala = chats.sala(chat_id)
    if sala is None: return "", 404
    return render_template("chat_tempo_real.html", sala = sala, usuario_logado = quem_esta_logado())

# O chat propriamente dito.

@app.route("/chat/<int:chat_id>/desde/<int:last_msg_id>")
@apenas_usuarios_logados
def mensagens(chat_id: int, last_msg_id: int) -> str | tuple[str, int]:
    sala = chats.sala(chat_id)
    if sala is None: return "", 404
    return sala.desde(last_msg_id).json

@app.route("/chat/<int:chat_id>", methods = ["POST"])
@apenas_usuarios_logados
def postar(chat_id: int) -> str | tuple[str, int]:
    texto = request.data.decode("utf-8")
    sala = chats.sala(chat_id)
    if sala is None: return "", 404
    logado = cast(InformacoesUsuarioSemSenha, quem_esta_logado())
    sala.postar(logado, texto)
    return ""

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 1234, debug = True)