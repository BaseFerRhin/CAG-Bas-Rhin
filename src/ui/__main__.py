"""Launch the Dash web application: python -m src.ui"""

from .app import create_app


def main() -> None:
    app = create_app()
    app.run(debug=False, port=8051, host="127.0.0.1")


if __name__ == "__main__":
    main()
