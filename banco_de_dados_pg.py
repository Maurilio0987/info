import pg8000
from urllib.parse import urlparse
import hashlib


def sha256(texto):
    sha = hashlib.sha256()
    sha.update(texto.encode('utf-8'))
    return sha.hexdigest()


class DatabaseManager:
    def __init__(self, db_url):
        self.db_url = db_url
    
        self.executar("""SET TIME ZONE 'America/Sao_Paulo'""")
        self.executar("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            usuario VARCHAR(255) UNIQUE NOT NULL,
            senha_hash CHAR(64) NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        
        self.executar("""
        CREATE TABLE IF NOT EXISTS produtos (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_compra NUMERIC(10, 2) NOT NULL,
            preco_venda NUMERIC(10, 2) NOT NULL
        )
        """)

        self.executar("""
        CREATE TABLE IF NOT EXISTS vendas (
            id SERIAL PRIMARY KEY,
            produto_id INTEGER,
            valor NUMERIC(10, 2) NOT NULL,
            quantidade INTEGER NOT NULL,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE SET NULL
        );
        """)

        self.executar("""
        CREATE TABLE IF NOT EXISTS historico (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER,
            acao VARCHAR(100),
            descricao TEXT,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_usuario_id FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );
        """)
        
        
    def conectar_banco_de_dados(self):
        parsed_url = urlparse(self.db_url)

        conexão = pg8000.connect(
            user=parsed_url.username,
            password=parsed_url.password,
            host=parsed_url.hostname,
            port=parsed_url.port or 5432,
            database=parsed_url.path.lstrip('/'),
            ssl_context=True  # Render exige SSL
        )
        conexão.autocommit = True  # Ativa autocommit
        return conexão

    
    def executar(self, query):
        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()
        cursor.execute(query)
        cursor.close()
        conexão.close()


    def verificar_usuario(self, usuario):
        query = "SELECT EXISTS (SELECT 1 FROM usuarios WHERE usuario = %s);"
        
        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()
        cursor.execute(query, (usuario,))
        resultado = cursor.fetchone()
        cursor.close()
        conexão.close()
        
        return resultado[0]


    def verificar_senha(self, usuario, senha):
        query = "SELECT senha_hash FROM usuarios WHERE usuario = %s;"
        
        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()
        cursor.execute(query, (usuario,))
        resultado = cursor.fetchone()
        cursor.close()
        conexão.close()
        
        if resultado:
            return resultado[0] == senha
        else:
            return False

    def adicionar_usuario(self, usuario, senha):
        query = "INSERT INTO usuarios (usuario, senha_hash) VALUES (%s, %s);"
        
        conexao = self.conectar_banco_de_dados()
        cursor = conexao.cursor()
        cursor.execute(query, (usuario, senha))
        cursor.close()
        conexao.close()


    def usuario(self, usuario):
        query = "SELECT id FROM usuarios WHERE usuario = %s;"
        
        conexao = self.conectar_banco_de_dados()
        cursor = conexao.cursor()
        cursor.execute(query, (usuario,))
        resultado = cursor.fetchone()
        cursor.close()
        conexao.close()

        return resultado[0] if resultado else None

    def tabela(self, tabela):
        query = f"SELECT * FROM {tabela};"

        conexão = self.conectar_banco_de_dados()
        cursor = conexão.cursor()
        cursor.execute(query)
        linhas = cursor.fetchall()
        cursor.close()
        conexão.close()
        return linhas

    def registrar_historico(self, usuario_id, acao, descricao):
        query = "INSERT INTO historico (usuario_id, acao, descricao) VALUES (%s, %s, %s);"

        conexao = self.conectar_banco_de_dados()
        cursor = conexao.cursor()
        cursor.execute(query, (usuario_id, acao, descricao))
        cursor.close()
        conexao.close()


    def adicionar_produto(self, nome, quantidade, preco_compra, preco_venda):
        query = "INSERT INTO produtos (nome, quantidade, preco_compra, preco_venda) VALUES (%s, %s, %s, %s);"

        conexao = self.conectar_banco_de_dados()
        cursor = conexao.cursor()
        cursor.execute(query, (nome, quantidade, preco_compra, preco_venda))
        cursor.close()
        conexao.close()

    def remover_produto(self, produto_id):
        query = "DELETE FROM produtos WHERE id = %s;"

        conexao = self.conectar_banco_de_dados()
        cursor = conexao.cursor()
        cursor.execute(query, (produto_id,))
        cursor.close()
        conexao.close()


    def atualizar_produto(self, produto_id, nome, quantidade, preco_compra, preco_venda):
        query = """
        UPDATE produtos 
        SET nome = %s, quantidade = %s, preco_compra = %s, preco_venda = %s
        WHERE id = %s;
        """

        conexao = self.conectar_banco_de_dados()
        cursor = conexao.cursor()
        cursor.execute(query, (nome, quantidade, preco_compra, preco_venda, produto_id))
        cursor.close()
        conexao.close()

    def registrar_venda(self, produto_id, quantidade, valor):
        query = """
            INSERT INTO vendas (produto_id, quantidade, valor, data)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP);
        """
        query_atualizar_produto = """
                UPDATE produtos
                SET quantidade = quantidade - %s
                WHERE id = %s;
            """
        conexao = self.conectar_banco_de_dados()
        cursor = conexao.cursor()
        cursor.execute(query, (produto_id, quantidade, valor))
        cursor.execute(query_atualizar_produto, (quantidade, produto_id))
        cursor.close()
        conexao.close()

    def vendas(self):
        query_vendas = """SELECT 
                            produtos.nome,
                            vendas.valor,
                            vendas.quantidade,
                            vendas.data
                        FROM vendas
                        JOIN produtos ON produtos.id=vendas.produto_id"""
        query_valor = """SELECT 
                            SUM(vendas.valor*vendas.quantidade), 
                            SUM(produtos.preco_compra*vendas.quantidade),
                            SUM((vendas.valor-produtos.preco_compra)*vendas.quantidade) 
                        FROM vendas
                        JOIN produtos ON produtos.id=vendas.produto_id"""


        conexao = self.conectar_banco_de_dados()
        cursor = conexao.cursor()
        cursor.execute(query_vendas)
        tabela = cursor.fetchall()
        cursor.execute(query_valor)
        
        saldo, despesas, lucro = cursor.fetchone()
        return [saldo, despesas, lucro, tabela]



if __name__ == "__main__":
    db_url = "postgresql://info_db_lsba_user:cdItHM06j2EdUB4UOiRRK56GdbiFTvUT@dpg-d0v2q3h5pdvs7382be30-a.oregon-postgres.render.com/info_db_lsba"
    db = DatabaseManager(db_url)
    