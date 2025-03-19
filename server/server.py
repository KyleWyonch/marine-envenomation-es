from flask import Flask, request, jsonify, make_response, send_from_directory
import sqlite3
from rapidfuzz import fuzz
from flask_cors import CORS
import logging
import os

# React static files will be served from here:
app = Flask(__name__, static_folder='../client/build', static_url_path='/')
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

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
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    conn = sqlite3.connect(os.path.join(BASE_DIR, "knowledge-base-recursive.db"))
    cursor = conn.cursor()
    symptoms_list = user_symptoms.lower().split()

    cursor.execute("""
        SELECT s.species_id, s.common_name, s.scientific_name, s.reference, es.symptom, es.onset_time, es.duration
        FROM Envenomation_Symptoms es
        JOIN Species s ON es.species_id = s.species_id
    """)
    rows = cursor.fetchall()

    if not rows:
        conn.close()
        return "No species data found in the database."

    probable_species = []

    for row in rows:
        species_id, common_name, scientific_name, reference, symptom, onset_time, duration = row
        combined_text = f"{symptom} {onset_time} {duration}"
        match_score = fuzzy_match(symptoms_list, combined_text)

        if match_score > 30:
            probable_species.append({
                "SpeciesID": species_id,
                "CommonName": common_name,
                "ScientificName": scientific_name,
                "Reference": reference if reference else "No reference available",
                "Symptom": symptom,
                "OnsetTime": onset_time,
                "Duration": duration,
                "MatchScore": match_score
            })

    if not probable_species:
        conn.close()
        return "No matching species found. Try refining your symptom description."

    probable_species.sort(key=lambda x: x["MatchScore"], reverse=True)

    treatments = {}
    for species in probable_species:
        species_id = species["SpeciesID"]
        cursor.execute("""
            SELECT FirstAidImmediateCare, MedicalInterventions, SpecializedTreatments
            FROM TreatmentProtocols
            WHERE SpeciesID = ?
        """, (species_id,))
        treatment_data = cursor.fetchone()
        if treatment_data:
            treatments[species["CommonName"]] = {
                "First Aid": treatment_data[0],
                "Medical Interventions": treatment_data[1],
                "Specialized Treatments": treatment_data[2]
            }

    conn.close()

    result_lines = ["Probable Species and Recommended Treatments:"]
    for species in probable_species:
        species_name = species["CommonName"]
        scientific_name = species["ScientificName"]
        match_score = species["MatchScore"]
        reference = species["Reference"]
        result_lines.append(f"\nSpecies: {species_name} ({scientific_name})")
        result_lines.append(f"- Match Score: {match_score}%")
        result_lines.append(f"- Symptom: {species['Symptom']}")
        result_lines.append(f"- Onset Time: {species['OnsetTime']}")
        result_lines.append(f"- Duration: {species['Duration']}")
        result_lines.append(f"- Reference: {reference}")
        if species_name in treatments:
            treatment = treatments[species_name]
            result_lines.append("\n**Recommended Treatment:**")
            result_lines.append(f"- First Aid: {treatment['First Aid']}")
            result_lines.append(f"- Medical Interventions: {treatment['Medical Interventions']}")
            result_lines.append(f"- Specialized Treatments: {treatment['Specialized Treatments']}")
        result_lines.append("=" * 80)

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

if __name__ == '__main__':
    app.run()
