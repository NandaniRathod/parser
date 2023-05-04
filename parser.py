from flask import Flask, render_template, request, send_file
from resume_parser import resumeparse
import os
from werkzeug.utils import secure_filename
import gender_guesser.detector as gender

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'UPLOAD_FOLDER'

@app.route('/')
def index():
    return render_template('resume_parser.html')

@app.route('/result', methods=['POST'])
def upload_resume():
    resume_file = request.files['resume']
    if resume_file:
        # Save the uploaded file to a directory
        filename = secure_filename(resume_file.filename)
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        resume_file.save(resume_path)

        # Parse the resume file
        data = resumeparse.read_file(resume_path)

        # Determine gender based on first name
        if data.get('name'):
            first_name = data['name'].split(' ')[0]
            gender_detector = gender.Detector()
            gender_value = gender_detector.get_gender(first_name)
            data['gender'] = gender_value

        # Render the resume data in a new HTML template
        return render_template('candidateOutput.html', data=data, resume_filename=filename)
    else:
        return "No resume file was uploaded."

@app.route('/download/<filename>')
def download_resume(filename):
    # Get the path to the uploaded resume file
    resume_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Download the resume file
    return send_file(resume_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)