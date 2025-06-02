from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
import os
from banco_de_dados_pg import DatabaseManager, sha256
from pytz import timezone



app = Flask(__name__)
app.secret_key = 'chave_secreta'  


db_url = "postgresql://info_db_lsba_user:cdItHM06j2EdUB4UOiRRK56GdbiFTvUT@dpg-d0v2q3h5pdvs7382be30-a.oregon-postgres.render.com/info_db_lsba"
db = DatabaseManager(db_url)



#               #   
#-----LOGIN-----#
#               #


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def index():
    if session.get("usuario") == "admin@admin": return redirect(url_for("admin"))
    elif session.get("usuario"): return redirect(url_for("principal"))
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    usuario = request.form["usuario"]
    senha = request.form["senha"]
    #if usuario == "adm" and senha == "adm":
    #    session["usuario"] = usuario
    #    return redirect(url_for("admin"))
    erro = None    
        
    if db.verificar_usuario(usuario):
        if db.verificar_senha(usuario, sha256(senha)):
            session["usuario"] = usuario
            return redirect(url_for("principal"))
        else:
            erro = "senha incorreta"
    else:
        erro = "usuario n~ao encontrado"

    return render_template("login.html", erro=erro)


@app.route("/logout")
@login_required
def logout():
    session.pop("usuario", None)
    return redirect(url_for("index"))




@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "GET":
        return render_template("cadastro.html")

    elif request.method == "POST":
        erro = None
        usuario = request.form["usuario"]
        senha = request.form["senha"]
        if not db.verificar_usuario(usuario):
            db.adicionar_usuario(usuario, sha256(senha))
            return redirect(url_for("index"))
        else:
            erro = "usuario ja cadastrado"
        return render_template("cadastro.html", erro=erro)




@app.route("/principal")
@login_required
def principal():
    return render_template("principal.html")





#app.run(debug=True, host="127.0.0.1", port=7000)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
