"""Launch the Dash web application: python -m src.ui"""

from .app import create_app


def main() -> None:
    app = create_app()
    app.run(debug=True, port=8051)


if __name__ == "__main__":
    main()
