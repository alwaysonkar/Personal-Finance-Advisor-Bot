"""Entry point. Run with:  python app.py"""
from flask import Flask

from database import init_db
from routes import bp


def create_app():
    app = Flask(__name__)
    app.register_blueprint(bp)

    # Create the database file when the application starts
    init_db()

    return app


# run_public.py imports this object
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
