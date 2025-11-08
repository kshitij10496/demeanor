import os

from flask import Flask, render_template, request, send_file

from main import TICKERS, analyze_index_for_web

app = Flask(__name__)


@app.route("/")
def index():
    """Display form to select an index."""
    return render_template("index.html", tickers=TICKERS.keys())


@app.route("/analyze", methods=["POST"])
def analyze():
    """Analyze selected index and display results."""
    index_name = request.form.get("index")

    if not index_name or index_name not in TICKERS:
        return "Invalid index selected", 400

    # Run analysis (uses date-based caching)
    result = analyze_index_for_web(index_name)

    return render_template("results.html", result=result)


@app.route("/plot/<index_name>")
def serve_plot(index_name):
    """Serve the z-score plot image."""
    import time

    today = time.strftime("%Y-%m-%d")
    plot_path = f"output/{index_name}/{today}_z_scores.png"

    if os.path.exists(plot_path):
        return send_file(plot_path, mimetype="image/png")
    else:
        return "Plot not found", 404


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8000)
