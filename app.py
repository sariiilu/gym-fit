import os
from datetime import date
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

import notion_client_ as nc

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

APP_PASSWORD = os.environ.get("APP_PASSWORD", "changeme")

ZIEL_OPTIONS = ["Oberkörper", "Unterkörper", "Ganzkörper", "Push", "Pull", "Cardio", "Mobility/Reha"]
KATEGORIE_OPTIONS = ["Beine", "Rücken", "Brust", "Schulter", "Arme", "Core", "Cardio", "Funktional", "Kurs", "Eigene"]
BEWERTUNG_OPTIONS = ["Zu leicht", "Locker", "Passend", "Moderat", "Zu schwer", "Hart"]
TYP_OPTIONS = ["Gerät/Übung", "Kurs"]


# ---------- Auth ----------

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("authed"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return wrapper


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pw = request.form.get("password", "")
        if pw == APP_PASSWORD:
            session["authed"] = True
            session.permanent = True
            nxt = request.args.get("next") or url_for("dashboard")
            return redirect(nxt)
        flash("Falsches Passwort.", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.errorhandler(nc.NotionError)
def handle_notion_error(e):
    flash(f"Notion-Fehler: {e}", "error")
    return redirect(request.referrer or url_for("dashboard"))


# ---------- Dashboard ----------

@app.route("/")
@login_required
def dashboard():
    sessions_raw = nc.query_data_source(
        nc.DS_SESSIONS,
        sorts=[{"property": "Datum", "direction": "descending"}],
        page_size=8,
    )
    recent_sessions = [nc.extract_properties(p) for p in sessions_raw]

    weight_raw = nc.query_data_source(
        nc.DS_BODYWEIGHT,
        sorts=[{"property": "Datum", "direction": "descending"}],
        page_size=1,
    )
    recent_weight = nc.extract_properties(weight_raw[0]) if weight_raw else None

    weight_first = nc.query_data_source(
        nc.DS_BODYWEIGHT,
        sorts=[{"property": "Datum", "direction": "ascending"}],
        page_size=1,
    )
    start_weight = nc.extract_properties(weight_first[0]) if weight_first else None

    all_sessions_count = len(nc.query_data_source(nc.DS_SESSIONS, page_size=100))

    return render_template(
        "dashboard.html",
        recent_sessions=recent_sessions,
        recent_weight=recent_weight,
        start_weight=start_weight,
        session_count=all_sessions_count,
    )


# ---------- Sessions (Trainings) ----------

@app.route("/sessions")
@login_required
def sessions_list():
    raw = nc.query_data_source(nc.DS_SESSIONS, sorts=[{"property": "Datum", "direction": "descending"}])
    sessions = [nc.extract_properties(p) for p in raw]
    return render_template("sessions_list.html", sessions=sessions)


@app.route("/sessions/new", methods=["GET", "POST"])
@login_required
def session_new():
    if request.method == "POST":
        properties = {
            "Session": nc.title_prop(request.form["title"]),
            "Datum": nc.date_prop(request.form["date"]),
            "Dauer (Min)": nc.number_prop(request.form.get("duration_min")),
            "Gewicht (kg)": nc.number_prop(request.form.get("bodyweight_kg")),
            "RPE gesamt": nc.number_prop(request.form.get("rpe")),
            "Schlaf (Std)": nc.number_prop(request.form.get("sleep_h")),
            "Ziel": nc.multi_select_prop(request.form.getlist("ziel")),
            "Notizen": nc.rich_text_prop(request.form.get("notes")),
        }
        session_page = nc.create_page(nc.DS_SESSIONS, properties)
        session_id = session_page["id"]
        session_date = request.form["date"]

        names = request.form.getlist("ex_name")
        kategorien = request.form.getlist("ex_kategorie")
        typen = request.form.getlist("ex_typ")
        saetze = request.form.getlist("ex_saetze")
        wdh = request.form.getlist("ex_wdh")
        gewicht = request.form.getlist("ex_gewicht")
        dauer = request.form.getlist("ex_dauer")
        details = request.form.getlist("ex_details")
        bewertung = request.form.getlist("ex_bewertung")
        naechstes = request.form.getlist("ex_naechstes")

        for i, name in enumerate(names):
            if not name.strip():
                continue
            ex_properties = {
                "Übung": nc.title_prop(name),
                "Kategorie": nc.select_prop(kategorien[i] if i < len(kategorien) else None),
                "Typ": nc.select_prop(typen[i] if i < len(typen) else None),
                "Sätze": nc.number_prop(saetze[i] if i < len(saetze) else None),
                "Wiederholungen": nc.number_prop(wdh[i] if i < len(wdh) else None),
                "Gewicht (kg)": nc.number_prop(gewicht[i] if i < len(gewicht) else None),
                "Dauer (Min)": nc.number_prop(dauer[i] if i < len(dauer) else None),
                "Satz-Details": nc.rich_text_prop(details[i] if i < len(details) else None),
                "Bewertung": nc.select_prop(bewertung[i] if i < len(bewertung) else None),
                "Vorschlag nächstes Mal": nc.rich_text_prop(naechstes[i] if i < len(naechstes) else None),
                "Datum": nc.date_prop(session_date),
                "Session": nc.relation_prop([session_id]),
            }
            nc.create_page(nc.DS_EXERCISES, ex_properties)

        flash("Training in Notion gespeichert.", "success")
        return redirect(url_for("session_detail", session_id=session_id))

    return render_template(
        "session_form.html",
        today=date.today().isoformat(),
        ziel_options=ZIEL_OPTIONS,
        kategorie_options=KATEGORIE_OPTIONS,
        bewertung_options=BEWERTUNG_OPTIONS,
        typ_options=TYP_OPTIONS,
    )


@app.route("/sessions/<session_id>")
@login_required
def session_detail(session_id):
    page = nc.get_page(session_id)
    s = nc.extract_properties(page)

    ex_raw = nc.query_data_source(
        nc.DS_EXERCISES,
        filter={"property": "Session", "relation": {"contains": session_id}},
    )
    exercises = [nc.extract_properties(p) for p in ex_raw]
    return render_template("session_detail.html", s=s, exercises=exercises)


@app.route("/sessions/<session_id>/delete", methods=["POST"])
@login_required
def session_delete(session_id):
    # Zugehörige Übungen ebenfalls archivieren, damit nichts verwaist in Notion herumliegt
    ex_raw = nc.query_data_source(
        nc.DS_EXERCISES,
        filter={"property": "Session", "relation": {"contains": session_id}},
    )
    for ex in ex_raw:
        nc.update_page(ex["id"], archived=True)
    nc.update_page(session_id, archived=True)
    flash("Training in Notion archiviert.", "success")
    return redirect(url_for("sessions_list"))


# ---------- Körpergewicht ----------

@app.route("/progress", methods=["GET", "POST"])
@login_required
def progress():
    if request.method == "POST":
        entry_date = request.form["date"]
        # Vorhandenen Eintrag für dieses Datum suchen (Datum ist Titel-Property)
        existing = nc.query_data_source(
            nc.DS_BODYWEIGHT,
            filter={"property": "Datum", "title": {"equals": entry_date}},
            page_size=1,
        )
        properties = {
            "Datum": nc.title_prop(entry_date),
            "Gewicht (kg)": nc.number_prop(request.form.get("weight_kg")),
            "Körperfett (%)": nc.number_prop(request.form.get("bodyfat_pct")),
            "Notizen": nc.rich_text_prop(request.form.get("notes")),
        }
        if existing:
            nc.update_page(existing[0]["id"], properties=properties)
        else:
            nc.create_page(nc.DS_BODYWEIGHT, properties)
        flash("Gewichtseintrag in Notion gespeichert.", "success")

    raw = nc.query_data_source(nc.DS_BODYWEIGHT, sorts=[{"property": "Datum", "direction": "ascending"}])
    rows = [nc.extract_properties(p) for p in raw]
    return render_template("progress.html", rows=rows, today=date.today().isoformat())


# ---------- API für Charts ----------

@app.route("/api/weight")
@login_required
def api_weight():
    raw = nc.query_data_source(nc.DS_BODYWEIGHT, sorts=[{"property": "Datum", "direction": "ascending"}])
    rows = [nc.extract_properties(p) for p in raw]
    return jsonify([
        {"date": r.get("Datum"), "weight_kg": r.get("Gewicht (kg)")}
        for r in rows if r.get("Gewicht (kg)") is not None
    ])


@app.route("/api/exercise-progress")
@login_required
def api_exercise_progress():
    name = request.args.get("name", "")
    raw = nc.query_data_source(
        nc.DS_EXERCISES,
        filter={"property": "Übung", "title": {"equals": name}},
        sorts=[{"property": "Datum", "direction": "ascending"}],
    )
    rows = [nc.extract_properties(p) for p in raw]
    return jsonify([
        {"date": r.get("Datum"), "gewicht_kg": r.get("Gewicht (kg)"), "wiederholungen": r.get("Wiederholungen")}
        for r in rows
    ])


@app.route("/api/exercise-names")
@login_required
def api_exercise_names():
    raw = nc.query_data_source(nc.DS_EXERCISES, page_size=100)
    extracted = [nc.extract_properties(p) for p in raw]
    names = sorted({e.get("Übung") for e in extracted if e.get("Übung")})
    return jsonify(names)


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
