"""Application entry point."""
from flask_ui import app

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)