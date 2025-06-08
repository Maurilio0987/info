from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from functools import wraps
import os
from banco_de_dados_pg import DatabaseManager, sha256



app = Flask(__name__)
app.secret_key = 'chave_secreta'  


db_url = "postgresql://info_db_lsba_user:cdItHM06j2EdUB4UOiRRK56GdbiFTvUT@dpg-d0v2q3h5pdvs7382be30-a.oregon-postgres.render.com/info_db_lsba"
db = DatabaseManager(db_url)


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
        erro = "usuário não encontrado"

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
            erro = "usuário já cadastrado"
        return render_template("cadastro.html", erro=erro)




@app.route("/principal")
@login_required
def principal():
    return render_template("principal.html")


@app.route("/estoque")
@login_required
def estoque():
    produtos = db.tabela("produtos")
    return render_template("estoque.html", produtos=produtos)

@app.route("/adicionar_produto", methods=["POST"])
@login_required
def adicionar_produto():
    data = request.get_json()

    id_usuario = db.usuario(session["usuario"])

    nome = data.get("nome")
    quantidade = int(data.get("quantidade"))
    preco_compra = float(data.get("preco_compra"))
    preco_venda = float(data.get("preco_venda"))

    db.adicionar_produto(nome, quantidade, preco_compra, preco_venda)
    db.registrar_historico(
        id_usuario,
        "ADIÇÃO",
        f"{quantidade} unidades de {nome} (compra: {preco_compra}, venda: {preco_venda})"
    )

    produtos = db.tabela("produtos")

    return jsonify({"status": "sucesso", "produtos": produtos})



@app.route("/remover_produto", methods=["POST"])
def remover_produto():
    dados = request.get_json()
    produto_id = dados.get('id')
    id_usuario = db.usuario(session["usuario"])
    if produto_id is None:
        return jsonify({'status': 'erro', 'mensagem': 'ID não fornecido'})

    try:
        db.remover_produto(produto_id)
        db.registrar_historico(id_usuario, "REMOÇÃO", f"produto {produto_id} foi removido")
        produtos = db.tabela("produtos")
        return jsonify({'status': 'sucesso', 'produtos': produtos})
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)})


@app.route('/atualizar_produto', methods=['POST'])
@login_required
def atualizar_produto():
    dados = request.get_json()
    id_usuario = db.usuario(session["usuario"])

    produto_id = dados.get('id')
    nome = dados.get('nome')
    quantidade = int(dados.get('quantidade'))
    preco_compra = float(dados.get('preco_compra'))
    preco_venda = float(dados.get('preco_venda'))

    try:
        db.atualizar_produto(produto_id, nome, quantidade, preco_compra, preco_venda)
        db.registrar_historico(
            id_usuario,
            "ATUALIZAÇÃO",
            f"Produto ID {produto_id} atualizado para {nome}, {quantidade} unidades, compra: {preco_compra}, venda: {preco_venda}"
        )
        produtos = db.tabela('produtos')
        return jsonify({'status': 'sucesso', 'produtos': produtos})
    except Exception as e:
        print(e)
        return jsonify({'status': 'erro', 'mensagem': str(e)})




@app.route("/vendas")
@login_required
def vendas():
    produtos = db.tabela("produtos")
    return render_template("vendas.html", produtos=produtos)


@app.route("/registrar_venda", methods=["POST"])
@login_required
def registrar_venda():
    data = request.get_json()

    produto_id = data.get("produto_id")
    quantidade = int(data.get("quantidade"))
    preco = float(data.get("preco"))
    print(quantidade, preco)
    usuario_id = db.usuario(session["usuario"])

    try:
        # Registrar a venda no banco de dados
        db.registrar_venda(produto_id, quantidade, preco)

        # Registrar no histórico
        db.registrar_historico(
            usuario_id,
            "VENDA",
            f"{produto_id}|{quantidade}|{preco}"
        )

        return jsonify({"status": "sucesso"})

    except Exception as e:
        return jsonify({"status": "erro", "erro": str(e)})




@app.route("/historico")
@login_required
def historico():
    historico = db.tabela("historico")
    return render_template("historico.html", historico=historico)

@app.route("/financeiro")
@login_required
def financeiro():
    saldo, despesas, lucro, tabela = db.vendas()
    return render_template("financeiro.html", tabela=tabela, despesas=despesas, saldo=saldo, lucro=lucro)


app.run(debug=True, host="localhost", port=8000)


#if __name__ == "__main__":
#    port = int(os.environ.get("PORT", 5000))
#    app.run(host="0.0.0.0", port=port)
