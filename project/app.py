from flask import Flask, request, jsonify, render_template_string
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from textblob import Word
from difflib import get_close_matches

app = Flask(__name__)

# Load the diseases data from a JSON file
with open('disease.json') as f:
    diseases_data = json.load(f)

# Prepare the data for the classifier
symptoms_list = list(diseases_data.keys())
diseases_list = [diseases_data[key] for key in symptoms_list]

symptom_descriptions = symptoms_list
labels = [disease["disease"] for disease in diseases_list]

# Create a pipeline with TF-IDF and Naive Bayes classifier
pipeline = make_pipeline(
    TfidfVectorizer(),
    MultinomialNB()
)

# Train the classifier
pipeline.fit(symptom_descriptions, labels)

def find_close_matches(input_symptoms):
    words = input_symptoms.split()
    matches = []
    for word in words:
        close_match = get_close_matches(word, symptoms_list, n=1, cutoff=0.8)
        if close_match:
            matches.append(close_match[0])
        else:
            matches.append(word)
    return ' '.join(matches)

def correct_spelling(text):
    corrected_text = ' '.join([Word(word).correct() for word in text.split()])
    return corrected_text

def get_similar_diseases(symptom):
    similar_diseases = []
    for idx, desc in enumerate(symptom_descriptions):
        if symptom.lower() in desc.lower():
            similar_diseases.append(diseases_list[idx])
    return similar_diseases

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
          <label for="symptoms">Enter Symptoms</label><br>
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
    
    # Correct spelling in input symptoms
    corrected_symptoms = correct_spelling(input_symptoms)
    
    # Find close matches for symptoms
    matched_symptoms = find_close_matches(corrected_symptoms)
    
    # Debugging: Print the corrected and matched symptoms
    print(f"Corrected Symptoms: {corrected_symptoms}")
    print(f"Matched Symptoms: {matched_symptoms}")
    
    # Predict the disease using the trained classifier
    disease_prediction = pipeline.predict([matched_symptoms])[0]
    
    # Debugging: Print the disease prediction
    print(f"Disease Prediction: {disease_prediction}")
    
    # Find the index of the predicted disease
    if disease_prediction in labels:
        predicted_idx = labels.index(disease_prediction)
        best_match = diseases_list[predicted_idx]
    else:
        best_match = {
            "disease": "No disease found",
            "description": "The given symptoms do not match any known disease.",
            "medicine": "Not found"
        }
    
    # Find similar diseases
    similar_diseases = get_similar_diseases(corrected_symptoms)
    
    # If no similar diseases are found, add a default message
    if not similar_diseases:
        similar_diseases_message = [{"disease": "No similar diseases found", "description": "There are no similar diseases for the given symptoms."}]
    else:
        similar_diseases_message = [{"disease": disease["disease"], "description": disease["description"]} for disease in similar_diseases]
    
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
        input[type=text]:hover{
        background-color:lightblue;
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
            <li><strong>{{ disease['disease'] }}:</strong> {{ disease['description'] }}</li>
          {% endfor %}
        </ul>
      </body>
    </html>
    '''
    return render_template_string(form_html, result=result)

if __name__ == '__main__':
    app.run(debug=True)
