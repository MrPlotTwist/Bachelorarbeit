from dotenv import load_dotenv
import os
import json
from openai import OpenAI
from app.ai_integration.pdf_init import createReportPDF
from app.db.database import update_run_report, finish_run

def gpt_output(db_output, run_id):
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path=dotenv_path)

    api_key = os.getenv("OPENAI_API_KEY")

    #für docker integration
    reports_path = os.getenv("REPORTS_PATH", "./reports")
    os.makedirs(reports_path, exist_ok=True)

    print(f"api-key geladen: {api_key is not None}")

    client = OpenAI(api_key=api_key)

    run_info = db_output.get("run")
    targets = db_output.get("targets", [])

    prompt = f"""
        Ich gebe dir nun Rohdaten aus einer Datenbank, die bei einer automatisierten Schwachstellenanalyse einer Website entstanden sind.

        Die Daten bestehen aus:
        1. RUN-Metadaten zum gesamten Scanlauf
        2. TARGET-Blöcken, wobei jeder TARGET-Block eine analysierte URL mit Formularen, Schwachstellen und ggf. Credentials beschreibt

        Die Rohdaten sind kein fertiger Bericht. Sie können unvollständig, redundant oder technisch roh formatiert sein. Deine Aufgabe ist es, diese Informationen zu konsolidieren, fachlich einzuordnen und daraus einen verständlichen Sicherheitsbericht auf Deutsch zu erstellen.

        Anforderungen:
        - Analysiere alle TARGET-Blöcke einzeln und im Gesamtzusammenhang.
        - Identifiziere tatsächlich vorhandene Schwachstellen primär anhand des Bereichs "Vulnerabilities".
        - Nutze Informationen aus "Forms" und "Credentials" nur als unterstützenden Kontext.
        - Fasse doppelte oder offensichtlich identische Einträge sinnvoll zusammen.
        - Bewerte jede Schwachstelle mit einer nachvollziehbaren CVSS 4.0-Einschätzung.
        - Wenn Informationen für eine exakte Bewertung fehlen, weise klar darauf hin und triff nur vorsichtige Annahmen.
        - Übernimm vorhandene Severity-Werte nicht blind, sondern prüfe sie kritisch anhand der übrigen Daten.
        - Priorisiere die Schwachstellen nach Risiko und Handlungsbedarf.
        - Erkläre jede Schwachstelle zusätzlich in verständlicher Sprache für nicht technikaffine Personen.
        - Erfinde keine Informationen, die nicht aus den Rohdaten ableitbar sind.

        Die Ausgabe soll folgende Abschnitte enthalten:
        1. Management-Zusammenfassung
        2. Technischer Überblick über die analysierten Seiten
        3. Priorisierte Liste der gefundenen Schwachstellen
        4. Detailanalyse pro Schwachstelle
        5. Konkrete Handlungsempfehlungen
        6. Gesamtfazit

        Für jede Schwachstelle beschreibe:
        - betroffene Seite bzw. URL
        - Typ der Schwachstelle
        - technische Beobachtung
        - mögliche Auswirkungen
        - geschätzte CVSS 4.0-Bewertung
        - Priorität
        - empfohlene Gegenmaßnahmen
        - leicht verständliche Erklärung

        RUN-METADATEN:
        {json.dumps(run_info, ensure_ascii=False, indent=2, default=str)}

        TARGET-BLÖCKE:
        {json.dumps(targets, ensure_ascii=False, indent=2, default=str)}
    """

    response = client.responses.create(
        model="gpt-5.4",
        input=prompt
    )

    print(response.output_text)

    try:
        report_filename = f"SecurityReport{run_id}.pdf"
        output_path = os.path.join(reports_path, report_filename)

        #response in PDF speichern
        createReportPDF(result=response.output_text, output_path=output_path)
        update_run_report(run_id=run_id, report_filename=output_path)
        finish_run(run_id=run_id)

        return {
            "report_filename": report_filename,
            "report_path": output_path,
            "report_text": response.output_text
        }

    except Exception as e:
        print("Fehler beim PDF-Erstellen:", repr(e))

        fallback_path = os.path.join(reports_path, f"SecurityReport{run_id}_fallback.txt")
        with open(fallback_path, "w", encoding="utf-8") as f:
            f.write(response.output_text or "")
        raise