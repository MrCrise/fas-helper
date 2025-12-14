"""
Frontend Application Server.

Этот модуль отвечает исключительно за отдачу статики (HTML, CSS, JS).
"""

from flask import Flask, render_template

# Инициализация Flask приложения.
# Flask автоматически ищет шаблоны в папке 'templates'
# и статические файлы (css, js) в папке 'static'.
app = Flask(__name__)


@app.route("/")
def index() -> str:
    """
    Главная страница (Single Page Application Entry Point).

    Рендерит базовый HTML-шаблон.

    Returns:
        str: Отрендеренный HTML шаблон 'index.html'.
    """
    return render_template("index.html")


if __name__ == "__main__":
    # Запуск сервера.
    print("Running at http://127.0.0.1:5000")
    app.run(debug=True, port=5000, host='0.0.0.0')