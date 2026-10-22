"""Servidor de desenvolvimento. Em produção use servir.py (waitress)."""
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Escuta só em 127.0.0.1 porque o debugger do Flask permite executar código.
    app.run(host='127.0.0.1', port=5000, debug=True)
