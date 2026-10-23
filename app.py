"""
WSGI application entry point for Vercel and production runners.
Exposes the Flask app instance from api_server.py.
"""
from api_server import app

if __name__ == "__main__":
    app.run()
