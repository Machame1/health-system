from flask import Flask, request, jsonify, render_template_string
import json
from textblob import Word
from difflib import get_close_matches
import re

app = Flask(__name__)

# Load the diseases data from a JSON file
with open('disease.json') as f:
    diseases_data = json.load(f)

symptoms_list = list(diseases_data.keys())
diseases_list = [diseases_data[key] for key in symptoms_list]

def split_and_correct_text(text):
    # Split concatenated words by finding word boundaries using regular expressions
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)  # Insert space between camel case
    text = re.sub(r"([a-z])([0-9])", r"\1 \2", text)  # Insert space before numbers
    text = re.sub(r"([0-9])([a-z])", r"\1 \2", text)  # Insert space after numbers
    text = re.sub(r"([A-Za-z])(\s+)([A-Za-z])", r"\1 \3", text)  # Remove extra spaces
    return text

def correct_spelling(text):
    # Correct spelling for each word in the text
    words = text.split()
    corrected_words = []
    for word in words:
        corrected_word = Word(word).correct()
        corrected_words.append(corrected_word)
    return ' '.join(corrected_words)

def find_close_matches(input_symptoms):
    # Attempt to match symptoms with known ones
    words = input_symptoms.split()
    matches = []
    for word in words:
        close_match = get_close_matches(word, symptoms_list, n=1, cutoff=0.8)
        if close_match:
            matches.append(close_match[0])
        else:
            matches.append(word)
    return ' '.join(matches)

def search_disease_by_symptoms(symptom):
    # Search for diseases based on corrected and matched symptoms
    found_diseases = []
    for disease_symptoms, disease_info in diseases_data.items():
        # Use partial matching to handle similar but not exact symptoms
        if re.search(r'\b' + re.escape(symptom.lower()) + r'\b', disease_symptoms.lower()):
            found_diseases.append(disease_info)
    return found_diseases

@app.route('/', methods=['GET'])
def index():
    form_html = '''
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Health Detecting System</title>
        <style>
        body{
            background-color:#f8f9fa;
            font-family: Arial, sans-serif;
            padding: 20px;
        }
        h1 {
            color: #007bff;
        }
        label {
            font-size: 1.2em;
        }
        input[type=text] {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            box-sizing: border-box;
        }
        input[type=submit] {
            background-color: #007bff;
            color: white;
            padding: 10px 20px;
            border: none;
            cursor: pointer;
        }
        input[type=submit]:hover {
            background-color: #0056b3;
        }
        </style>
      </head>
      <body>
        <h1>Health Detecting System</h1>
        <form action="/api/check_symptoms" method="post">
          <label for="symptoms">Enter Symptoms:</label><br>
          <input type="text" id="symptoms" name="symptoms" required><br><br>
          <input type="submit" value="Check Disease">
        </form>
      </body>
    </html>
    '''
    return render_template_string(form_html)

@app.route('/api/check_symptoms', methods=['POST'])
def check_symptoms():
    input_symptoms = request.form.get('symptoms', '')
    
    # Split and correct spelling in input symptoms
    split_corrected_symptoms = split_and_correct_text(input_symptoms)
    corrected_symptoms = correct_spelling(split_corrected_symptoms)
    
    # Find close matches for symptoms
    matched_symptoms = find_close_matches(corrected_symptoms)
    
    # Search for diseases that match the given symptoms
    matching_diseases = search_disease_by_symptoms(matched_symptoms)
    
    # If no diseases are found, return a default message
    if not matching_diseases:
        best_match = {
            "disease": "No disease found",
            "description": "The given symptoms do not match any known disease.",
            "medicine": "N/A"
        }
        similar_diseases_message = [{"disease": "No similar diseases found", "description": "There are no similar diseases for the given symptoms.", "medicine": "N/A"}]
    else:
        best_match = matching_diseases[0]
        similar_diseases_message = [{"disease": disease["disease"], "description": disease["description"], "medicine": disease["medicine"]} for disease in matching_diseases if disease["disease"] != best_match["disease"]]
    
    result = {
        "disease": best_match["disease"],
        "description": best_match["description"],
        "medicine": best_match["medicine"],
        "similar_diseases": similar_diseases_message
    }
    
    # Check if the request expects a JSON response
    if request.headers.get('Accept') == 'application/json':
        return jsonify(result)
    
    # Otherwise, render the result in HTML
    form_html = '''
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Health Detecting System</title>
        <style>
        body{
            background-color:#f8f9fa;
            font-family: Arial, sans-serif;
            padding: 20px;
        }
        h1 {
            color: #007bff;
        }
        label {
            font-size: 1.2em;
        }
        input[type=text] {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            box-sizing: border-box;
        }
        input[type=submit] {
            background-color: #007bff;
            color: white;
            padding: 10px 20px;
            border: none;
            cursor: pointer;
        }
        input[type=submit]:hover {
            background-color: blue;
        }
        h2 {
            color: #343a40;
        }
        p {
            font-size: 1.1em;
        }
        ul {
            list-style-type: none;
            padding: 0;
        }
        li {
            padding: 5px 0;
        }
        </style>
      </head>
      <body>
        <h1>Health Detecting System</h1>
        <form action="/api/check_symptoms" method="post">
          <label for="symptoms">Enter Symptoms:</label><br>
          <input type="text" id="symptoms" name="symptoms" required><br><br>
          <input type="submit" value="Check Disease">
        </form>
        <h2>Result</h2>
        <p><strong>Disease:</strong> {{ result['disease'] }}</p>
        <p><strong>Description:</strong> {{ result['description'] }}</p>
        <p><strong>Medicine:</strong> {{ result['medicine'] }}</p>
        <h2>Similar Diseases</h2>
        <ul>
          {% for disease in result['similar_diseases'] %}
            <li><u><strong>{{ disease['disease'] }}:</strong></u> {{ disease['description'] }}<br><strong>Medicine:</strong> {{ disease['medicine'] }}</li>
          {% endfor %}
        </ul>
      </body>
    </html>
    '''
    return render_template_string(form_html, result=result)

if __name__ == '__main__':
    app.run(debug=True)
