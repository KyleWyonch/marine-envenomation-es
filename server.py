from flask import Flask, request, jsonify
import sqlite3
from rapidfuzz import fuzz
from flask_cors import CORS
from flask import make_response
import logging

app = Flask(__name__)
CORS(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fuzzy_match(symptoms_list, text):
    """Calculate fuzzy match score between user symptoms and database text."""
    score = 0
    for symptom in symptoms_list:
        score += fuzz.partial_ratio(symptom.lower(), text.lower())
    return score

def infer_species_and_treatment(user_symptoms):
    conn = sqlite3.connect("./knowledge-base-mar-8")
    cursor = conn.cursor()

    # Split user symptoms for better matching
    symptoms_list = user_symptoms.lower().split()

    cursor.execute("""
        SELECT s.SpeciesID, s.CommonName, s.ScientificName, s.Reference, sym.LocalEffects, sym.SystemicEffects
        FROM Symptoms sym
        JOIN Species s ON sym.SpeciesID = s.SpeciesID
    """)

    rows = cursor.fetchall()

    if not rows:
        conn.close()
        return "No species data found in the database."

    probable_species = []

    # Apply fuzzy matching
    for row in rows:
        species_id, common_name, scientific_name, reference, local_effects, systemic_effects = row
        combined_text = f"{local_effects} {systemic_effects}"
        match_score = fuzzy_match(symptoms_list, combined_text)

        if match_score > 30:
            probable_species.append({
                "SpeciesID": species_id,
                "CommonName": common_name,
                "ScientificName": scientific_name,
                "Reference": reference if reference else "No reference available",
                "LocalEffects": local_effects,
                "SystemicEffects": systemic_effects,
                "MatchScore": match_score
            })

    if not probable_species:
        conn.close()
        return "No matching species found. Try refining your symptom description."

    # Sort by highest match score
    probable_species.sort(key=lambda x: x["MatchScore"], reverse=True)

    # Retrieve treatment protocols
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

    # Format the result
    result_lines = ["Probable Species and Recommended Treatments:"]
    for species in probable_species:
        species_name = species["CommonName"]
        scientific_name = species["ScientificName"]
        match_score = species["MatchScore"]
        reference = species["Reference"]
        result_lines.append(f"\nSpecies: {species_name} ({scientific_name})")
        result_lines.append(f"- Match Score: {match_score}%")
        result_lines.append(f"- Local Effects: {species['LocalEffects']}")
        result_lines.append(f"- Systemic Effects: {species['SystemicEffects']}")
        result_lines.append(f"- Reference: {reference}")
        if species_name in treatments:
            treatment = treatments[species_name]
            result_lines.append("\n**Recommended Treatment:**")
            result_lines.append(f"- First Aid: {treatment['First Aid']}")
            result_lines.append(f"- Medical Interventions: {treatment['Medical Interventions']}")
            result_lines.append(f"- Specialized Treatments: {treatment['Specialized Treatments']}")
        result_lines.append("=" * 80)

    return "\n".join(result_lines)

@app.route('/api/infer', methods=['POST', 'OPTIONS'])
def infer():
    if request.method == 'OPTIONS':
        # Handle preflight request manually
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

@app.route('/')
def index():
    return "Marine Envenomation Backend is Live!"

if __name__ == '__main__':
    app.run(debug=True)
