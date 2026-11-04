"""PhantomSignal Export Routes — report generation."""
import logging
import os

from flask import (
    Blueprint, after_this_request, current_app, flash, jsonify, redirect, render_template, request,
    send_file, url_for,
)
from phantomsignal.exporters.manager import ExportManager, ScanNotFound, UnsupportedFormat
from phantomsignal.core.database import get_db
from phantomsignal.core.models import Scan

export_bp = Blueprint("export", __name__)
logger = logging.getLogger("phantomsignal.web.export")


@export_bp.route("/<scan_id>")
def export_options(scan_id):
    with get_db() as db:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            flash("Scan not found.", "error")
            return redirect(url_for("scans.list_scans"))
        scan_dict = scan.to_dict()
    return render_template("export.html", scan=scan_dict)


@export_bp.route("/<scan_id>/generate", methods=["POST"])
def generate_export(scan_id):
    fmt = request.form.get("format", "json")
    compress = request.form.get("compress") == "on"
    encrypt = request.form.get("encrypt") == "on"
    password = request.form.get("password", "").strip() or None

    if encrypt and not password:
        flash("Encryption password required.", "error")
        return redirect(url_for("export.export_options", scan_id=scan_id))

    try:
        manager = ExportManager()
        result = manager.export(
            scan_id=scan_id,
            fmt=fmt,
            compress=compress,
            encrypt=encrypt,
            encryption_password=password,
        )

        @after_this_request
        def remove_download(response):
            """The browser now has its copy, so don't leave personal data on disk."""
            try:
                os.unlink(result["file_path"])
            except OSError as exc:
                current_app.logger.warning("Could not remove export file: %s", exc)
            return response

        return send_file(
            result["file_path"],
            as_attachment=True,
            download_name=result["file_name"],
        )
    except Exception as e:
        flash(f"Export failed: {e}", "error")
        return redirect(url_for("export.export_options", scan_id=scan_id))


@export_bp.route("/api/<scan_id>", methods=["POST"])
def api_export(scan_id):
    data = request.get_json() or {}
    try:
        manager = ExportManager()
        result = manager.export(
            scan_id=scan_id,
            fmt=data.get("format", "json"),
            compress=data.get("compress", False),
            encrypt=data.get("encrypt", False),
            encryption_password=data.get("password"),
        )
        return jsonify(result)
    except ScanNotFound:
        return jsonify({"error": "Scan not found."}), 404
    except UnsupportedFormat:
        available = ", ".join(ExportManager.SUPPORTED_FORMATS)
        return jsonify({"error": f"Unsupported format. Available: {available}."}), 400
    except Exception:
        logger.exception("Export of scan failed")
        return jsonify({"error": "Export failed. See the server log."}), 500
