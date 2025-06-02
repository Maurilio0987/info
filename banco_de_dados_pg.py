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
    

        self.executar("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            usuario VARCHAR(255) UNIQUE NOT NULL,
            senha_hash CHAR(64) NOT NULL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
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


if __name__ == "__main__":
    pass
    
