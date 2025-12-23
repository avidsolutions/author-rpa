#!/usr/bin/env python3
"""Flask web UI for RPA Framework."""

import os
import sys
import json
import tempfile
import traceback
from pathlib import Path
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from rpa import RPA
from rpa.core.pricing import PricingManager, PricingTier, get_pricing_table

app = Flask(__name__)
CORS(app)


# ============================================================
# Security Headers
# ============================================================

@app.before_request
def block_suspicious_requests():
    """Block requests that attempt to access source code or sensitive files."""
    blocked_patterns = [
        '.py', '.pyc', '.pyo',  # Python source files
        '.git', '.env',  # Git and environment files
        '__pycache__',  # Python cache
        '.yaml', '.yml',  # Config files
        'requirements.txt',  # Dependencies
    ]

    path = request.path.lower()
    for pattern in blocked_patterns:
        if pattern in path:
            return jsonify({"error": "Access denied"}), 403

    # Block requests with suspicious user agents (automated scraping tools)
    user_agent = request.headers.get('User-Agent', '').lower()
    blocked_agents = ['curl', 'wget', 'python-requests', 'scrapy', 'httpclient']
    for agent in blocked_agents:
        if agent in user_agent:
            # Allow API endpoints but block HTML pages
            if not request.path.startswith('/api/'):
                return jsonify({"error": "Access denied"}), 403

    return None


@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    # Content Security Policy - restrict resource loading
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )

    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'

    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # Enable XSS protection
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Referrer policy - don't leak referrer info
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Permissions policy - restrict browser features
    response.headers['Permissions-Policy'] = (
        'geolocation=(), microphone=(), camera=(), '
        'payment=(), usb=(), magnetometer=(), gyroscope=()'
    )

    # Cache control for sensitive pages
    if 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

    return response

# Initialize RPA
bot = RPA()

# Temp directory for file operations
UPLOAD_FOLDER = tempfile.mkdtemp()
OUTPUT_FOLDER = tempfile.mkdtemp()


@app.route("/")
def index():
    """Main dashboard."""
    return render_template("index.html")


# ============================================================
# Spreadsheet Module
# ============================================================

@app.route("/spreadsheet")
def spreadsheet_page():
    return render_template("spreadsheet.html")


@app.route("/api/spreadsheet/read", methods=["POST"])
def spreadsheet_read():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        df = bot.spreadsheet.read(filepath)
        data = df.to_dict(orient="records")
        columns = list(df.columns)

        return jsonify({
            "success": True,
            "data": data,
            "columns": columns,
            "rows": len(data),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/spreadsheet/write", methods=["POST"])
def spreadsheet_write():
    try:
        data = request.json.get("data", [])
        filename = request.json.get("filename", "output.csv")

        filepath = os.path.join(OUTPUT_FOLDER, filename)
        bot.spreadsheet.write(data, filepath)

        return jsonify({"success": True, "path": filepath})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# PDF Module
# ============================================================

@app.route("/pdf")
def pdf_page():
    return render_template("pdf.html")


@app.route("/api/pdf/extract", methods=["POST"])
def pdf_extract():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        text = bot.pdf.extract_text(filepath)
        info = bot.pdf.get_info(filepath)

        return jsonify({
            "success": True,
            "text": text,
            "info": info,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pdf/merge", methods=["POST"])
def pdf_merge():
    try:
        files = request.files.getlist("files")
        if len(files) < 2:
            return jsonify({"error": "Need at least 2 PDFs"}), 400

        filepaths = []
        for f in files:
            path = os.path.join(UPLOAD_FOLDER, f.filename)
            f.save(path)
            filepaths.append(path)

        output_path = os.path.join(OUTPUT_FOLDER, "merged.pdf")
        bot.pdf.merge(filepaths, output_path)

        return send_file(output_path, as_attachment=True, download_name="merged.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pdf/create", methods=["POST"])
def pdf_create():
    try:
        text = request.json.get("text", "")
        title = request.json.get("title", "Document")

        output_path = os.path.join(OUTPUT_FOLDER, "document.pdf")
        bot.pdf.create_from_text(text, output_path, title=title)

        return send_file(output_path, as_attachment=True, download_name="document.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# Documentation Module
# ============================================================

@app.route("/docs")
def docs_page():
    return render_template("docs.html")


@app.route("/api/docs/create-word", methods=["POST"])
def docs_create_word():
    try:
        title = request.json.get("title", "Document")
        content = request.json.get("content", "")

        output_path = os.path.join(OUTPUT_FOLDER, "document.docx")
        bot.docs.create_word(output_path, title=title, content=content)

        return send_file(output_path, as_attachment=True, download_name="document.docx")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/docs/create-markdown", methods=["POST"])
def docs_create_markdown():
    try:
        title = request.json.get("title", "Document")
        sections = request.json.get("sections", [])

        output_path = os.path.join(OUTPUT_FOLDER, "document.md")
        bot.docs.create_markdown(output_path, title, sections)

        return send_file(output_path, as_attachment=True, download_name="document.md")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/docs/markdown-to-html", methods=["POST"])
def docs_markdown_to_html():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)

        output_path = os.path.join(OUTPUT_FOLDER, "document.html")
        bot.docs.markdown_to_html(filepath, output_path)

        return send_file(output_path, as_attachment=True, download_name="document.html")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# Web Scraper Module
# ============================================================

@app.route("/scraper")
def scraper_page():
    return render_template("scraper.html")


@app.route("/api/scraper/extract-text", methods=["POST"])
def scraper_extract_text():
    try:
        url = request.json.get("url")
        selector = request.json.get("selector")

        if not url:
            return jsonify({"error": "URL required"}), 400

        text = bot.scraper.extract_text(url, selector=selector if selector else None)

        return jsonify({"success": True, "text": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/scraper/extract-links", methods=["POST"])
def scraper_extract_links():
    try:
        url = request.json.get("url")
        if not url:
            return jsonify({"error": "URL required"}), 400

        links = bot.scraper.extract_links(url)

        return jsonify({"success": True, "links": links})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/scraper/extract-table", methods=["POST"])
def scraper_extract_table():
    try:
        url = request.json.get("url")
        if not url:
            return jsonify({"error": "URL required"}), 400

        table = bot.scraper.extract_table(url)

        return jsonify({"success": True, "table": table})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# API Module
# ============================================================

@app.route("/api-client")
def api_client_page():
    return render_template("api_client.html")


@app.route("/api/api-client/request", methods=["POST"])
def api_client_request():
    try:
        method = request.json.get("method", "GET")
        url = request.json.get("url")
        headers = request.json.get("headers", {})
        body = request.json.get("body")

        if not url:
            return jsonify({"error": "URL required"}), 400

        # Configure API module
        bot.api.configure(headers=headers)

        if method == "GET":
            result = bot.api.get(url)
        elif method == "POST":
            result = bot.api.post(url, json=body)
        elif method == "PUT":
            result = bot.api.put(url, json=body)
        elif method == "DELETE":
            result = {"success": bot.api.delete(url)}
        else:
            return jsonify({"error": f"Unsupported method: {method}"}), 400

        return jsonify({"success": True, "response": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# Database Module
# ============================================================

@app.route("/database")
def database_page():
    return render_template("database.html")


@app.route("/api/database/connect", methods=["POST"])
def database_connect():
    try:
        connection_string = request.json.get("connection_string")
        if not connection_string:
            return jsonify({"error": "Connection string required"}), 400

        bot.database.connect(connection_string)
        tables = bot.database.get_tables()

        return jsonify({"success": True, "tables": tables})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/database/query", methods=["POST"])
def database_query():
    try:
        query = request.json.get("query")
        if not query:
            return jsonify({"error": "Query required"}), 400

        results = bot.database.execute(query)

        return jsonify({"success": True, "results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/database/tables", methods=["GET"])
def database_tables():
    try:
        tables = bot.database.get_tables()
        return jsonify({"success": True, "tables": tables})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# Files Module
# ============================================================

@app.route("/files")
def files_page():
    return render_template("files.html")


@app.route("/api/files/list", methods=["POST"])
def files_list():
    try:
        directory = request.json.get("directory", ".")
        pattern = request.json.get("pattern", "*")

        files = bot.files.list_files(directory, pattern)
        file_info = [bot.files.get_info(str(f)) for f in files[:100]]  # Limit to 100

        return jsonify({"success": True, "files": file_info})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/files/read", methods=["POST"])
def files_read():
    try:
        path = request.json.get("path")
        if not path:
            return jsonify({"error": "Path required"}), 400

        content = bot.files.read_text(path)
        return jsonify({"success": True, "content": content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# Workflow Module
# ============================================================

@app.route("/workflow")
def workflow_page():
    return render_template("workflow.html")


@app.route("/api/workflow/run", methods=["POST"])
def workflow_run():
    try:
        steps = request.json.get("steps", [])

        workflow = bot.workflow("Custom Workflow")

        results = []
        for step in steps:
            step_type = step.get("type")
            params = step.get("params", {})

            if step_type == "scrape":
                workflow.add_step(
                    f"Scrape {params.get('url', '')}",
                    lambda p=params: bot.scraper.extract_text(p.get("url"), p.get("selector"))
                )
            elif step_type == "api":
                workflow.add_step(
                    f"API {params.get('method', 'GET')} {params.get('url', '')}",
                    lambda p=params: bot.api.get(p.get("url")) if p.get("method") == "GET" else bot.api.post(p.get("url"), json=p.get("body"))
                )

        result = workflow.run()
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


# ============================================================
# Desktop Module (limited in web context)
# ============================================================

@app.route("/desktop")
def desktop_page():
    return render_template("desktop.html")


@app.route("/api/desktop/screenshot", methods=["POST"])
def desktop_screenshot():
    try:
        output_path = os.path.join(OUTPUT_FOLDER, "screenshot.png")
        bot.desktop.screenshot(output_path)
        return send_file(output_path, mimetype="image/png")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/desktop/screen-size", methods=["GET"])
def desktop_screen_size():
    try:
        size = bot.desktop.get_screen_size()
        return jsonify({"success": True, "width": size[0], "height": size[1]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# Pricing Module
# ============================================================

@app.route("/pricing")
def pricing_page():
    return render_template("pricing.html")


@app.route("/api/pricing/plans", methods=["GET"])
def get_plans():
    """Get all available pricing plans."""
    try:
        plans = get_pricing_table()
        return jsonify({"success": True, "plans": plans})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/pricing/plan/<tier>", methods=["GET"])
def get_plan(tier):
    """Get a specific pricing plan."""
    try:
        tier_enum = PricingTier(tier)
        plan = PricingManager.get_plan(tier_enum)
        return jsonify({
            "success": True,
            "plan": {
                "tier": plan.tier.value,
                "name": plan.name,
                "description": plan.description,
                "monthly_price": plan.monthly_price_usd,
                "annual_price": plan.annual_price_usd,
                "marketplace_sku": plan.marketplace_sku,
            }
        })
    except ValueError:
        return jsonify({"error": f"Invalid tier: {tier}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Autho.R - Robotic Process Automation")
    print("=" * 60)
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Output folder: {OUTPUT_FOLDER}")
    print("Starting server at http://localhost:8080")
    print("=" * 60)

    app.run(debug=True, host="0.0.0.0", port=8080)
