import os
import json
from datetime import date
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, request, jsonify, session, send_file
import io

import scraper
import ai_generator
import exporter

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-me")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/crawl", methods=["POST"])
def crawl():
    data = request.get_json()
    url = (data.get("url") or "").strip()
    max_products = int(data.get("max_products") or 30)
    max_products = max(5, min(50, max_products))

    if not url:
        return jsonify({"error": "Please enter a store URL."}), 400

    result = scraper.crawl(url, max_products)

    if "error" in result:
        return jsonify(result), 400

    if not result.get("products"):
        return jsonify({"error": "No products were found on this page. Try a different URL (e.g. the /products or /shop page)."}), 400

    session["store_data"] = result
    return jsonify({
        "store_name": result["store_name"],
        "product_count": result["product_count"],
        "products": result["products"][:10],
        "categories": result["categories"],
    })


@app.route("/generate", methods=["POST"])
def generate():
    store_data = session.get("store_data")
    if not store_data:
        return jsonify({"error": "No store data found. Please crawl a store first."}), 400

    data = request.get_json()
    tone = data.get("tone", "Friendly")
    language = data.get("language", "English")

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or api_key == "your-api-key-here":
        return jsonify({"error": "API key not configured. Please open the .env file and paste your Claude API key."}), 400

    try:
        strategy = ai_generator.generate_strategy(store_data, tone=tone, language=language)
    except Exception as e:
        return jsonify({"error": f"AI generation failed: {str(e)}"}), 500

    session["strategy"] = strategy
    return jsonify({"strategy": strategy})


@app.route("/download")
def download():
    store_data = session.get("store_data")
    strategy = session.get("strategy")

    if not store_data or not strategy:
        return "No data to export. Please generate a strategy first.", 400

    try:
        docx_bytes = exporter.build_docx(store_data, strategy)
    except Exception as e:
        return f"Export failed: {str(e)}", 500

    store_name = store_data.get("store_name", "Store").replace(" ", "_")
    today = date.today().strftime("%Y-%m-%d")
    filename = f"{store_name}_Marketing_Strategy_{today}.docx"

    return send_file(
        io.BytesIO(docx_bytes),
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


if __name__ == "__main__":
    app.run(debug=False, port=5000)
