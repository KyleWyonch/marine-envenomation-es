from flask import Flask, request, jsonify, make_response, send_from_directory
import sqlite3
from rapidfuzz import fuzz
from flask_cors import CORS
import logging
import os

# React static files will be served from here:
app = Flask(__name__, static_folder='../client/build', static_url_path='/')
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === Your fuzzy matching logic ===
def fuzzy_match(symptoms_list, text):
    score = 0
    for symptom in symptoms_list:
        score += fuzz.partial_ratio(symptom.lower(), text.lower())
    return score

def infer_species_and_treatment(user_symptoms):
    conn = sqlite3.connect(os.path.join(BASE_DIR, "knowledge-base.db"))
    cursor = conn.cursor()
    symptoms_list = user_symptoms.lower().split()

    # Step 1: Match symptoms (now includes reference_id)
    cursor.execute("""
        SELECT es.species_id, es.reference_id, es.symptom, es.onset_time, es.duration
        FROM Envenomation_Symptoms es
    """)
    rows = cursor.fetchall()

    if not rows:
        conn.close()
        return "No symptom data found in the database."

    probable_species = []

    for row in rows:
        species_id, reference_id, symptom, onset_time, duration = row
        combined_text = f"{symptom} {onset_time or ''} {duration or ''}"
        match_score = fuzzy_match(symptoms_list, combined_text)
        if match_score > 30:
            probable_species.append({
                "SpeciesID": species_id,
                "ReferenceID": reference_id,
                "Symptom": symptom,
                "OnsetTime": onset_time,
                "Duration": duration,
                "MatchScore": match_score
            })

    if not probable_species:
        conn.close()
        return "No matching species found. Try refining your symptom description."

    probable_species.sort(key=lambda x: x["MatchScore"], reverse=True)

    result_lines = ["Probable Species and Recommended Treatments:"]

    for species in probable_species:
        species_id = species["SpeciesID"]
        reference_id = species["ReferenceID"]

        # Step 2: Get common name
        cursor.execute("""
            SELECT common_name FROM Common_Names
            WHERE species_id = ? AND reference_id = ? LIMIT 1
        """, (species_id, reference_id))
        common_name = cursor.fetchone()
        species["CommonName"] = common_name[0] if common_name else "Unknown"

        # Step 3: Get reference DOI (new way)
        cursor.execute("SELECT doi FROM References_Table WHERE reference_id = ?", (reference_id,))
        reference = cursor.fetchone()
        species["Reference"] = reference[0] if reference else "No reference available"

        # Step 4: Get treatment info (from Treatment_Protocols)
        cursor.execute("""
            SELECT first_aid, hospital_treatment, prognosis
            FROM Treatment_Protocols
            WHERE species_id = ? AND reference_id = ?
        """, (species_id, reference_id))
        treatment_data = cursor.fetchone()
        if treatment_data:
            species["FirstAid"] = treatment_data[0]
            species["HospitalTreatment"] = treatment_data[1]
            species["Prognosis"] = treatment_data[2]

        # === Assemble output ===
        result_lines.append(f"\nSpecies: {species['CommonName']}")
        if species.get("Picture"):
            result_lines.append(f'<img src="/{species["Picture"]}" alt="{species["CommonName"]}" style="max-width:300px; border-radius:8px; margin-top:10px;" />')
        result_lines.append(f"- Match Score: {species['MatchScore']}%")
        result_lines.append(f"- Symptom: {species['Symptom']}")
        result_lines.append(f"- Onset Time: {species['OnsetTime']}")
        result_lines.append(f"- Duration: {species['Duration']}")
        if species["Reference"] != "No reference available":
            doi_url = f"https://dx.doi.org/{species['Reference']}"
            result_lines.append(f'- Reference: <a href="{doi_url}" target="_blank">[Ref]</a>')
        else:
            result_lines.append("- Reference: No reference available")
        if "FirstAid" in species:
            result_lines.append("\n**Recommended Treatment:**")
            result_lines.append(f"- First Aid: {species['FirstAid']}")
            result_lines.append(f"- Hospital Treatment: {species['HospitalTreatment']}")
            result_lines.append(f"- Prognosis: {species['Prognosis']}")
        result_lines.append("=" * 80)

    conn.close()
    return "\n".join(result_lines)

# === API Endpoint ===
@app.route('/api/infer', methods=['POST', 'OPTIONS'])
def infer():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        return response, 200

    data = request.get_json()
    if not data or 'symptoms' not in data:
        return jsonify({'error': 'Missing symptoms in request'}), 400
    symptoms = data['symptoms']
    result = infer_species_and_treatment(symptoms)
    return result, 200

# === Serve React frontend ===
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')
@app.route('/species_images/<path:filename>')
def serve_species_image(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'species_images'), filename)
