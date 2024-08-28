from flask import Flask, request, jsonify, render_template_string
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from textblob import Word

app = Flask(__name__)

with open('disease.json') as f:
    diseases_data = json.load(f)

symptoms_list = list(diseases_data.keys())
diseases_list = [diseases_data[key] for key in symptoms_list]

symptom_descriptions = symptoms_list
labels = [disease["disease"] for disease in diseases_list]

pipeline = make_pipeline(
    TfidfVectorizer(),
    MultinomialNB()
)

pipeline.fit(symptom_descriptions, labels)

def correct_spelling(text):
    corrected_text = ' '.join([Word(word).correct() for word in text.split()])
    return corrected_text

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
                background-image:url("doc.jpg")

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
    
    # Predict the disease using the trained classifier
    disease_prediction = pipeline.predict([corrected_symptoms])[0]
    
    # Find the index of the predicted disease
    predicted_idx = labels.index(disease_prediction)
    
    # Get the corresponding disease data
    best_match = diseases_list[predicted_idx]
    
    result = {
        "disease": best_match["disease"],
        "description": best_match["description"],
        "medicine": best_match["medicine"]
    }
    
    # Render the form with results
    form_html = '''
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Health Detecting System</title>
      </head>
      <body>
        <h1>Health Detecting System</h1>
        <form action="/api/check_symptoms" method="post">
          <label for="symptoms">Enter Symptoms (comma-separated):</label><br>
          <input type="text" id="symptoms" name="symptoms" required><br><br>
          <input type="submit" value="Check Disease">
        </form>
        <h2>Result</h2>
        <p><strong>Disease:</strong> {{ result['disease'] }}</p>
        <p><strong>Description:</strong> {{ result['description'] }}</p>
        <p><strong>Medicine:</strong> {{ result['medicine'] }}</p>
      </body>
    </html>
    '''
    return render_template_string(form_html, result=result)

if __name__ == '__main__':
    app.run(debug=True)
