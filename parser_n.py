from flask import Flask, request, render_template, jsonify
from resume_parser import resumeparse
from mysql.connector import connect, Error
import os
import time

app = Flask(__name__)

# Connect to the database
try:
    connection = connect(
        host='localhost',
        user='root',
        password='',
        database='resumes',
        connect_timeout=6000
    )
    print("Connection established!")
except Error as e:
    print(f"Error connecting to the database: {e}")

# Create a table to store the resume information
with connection.cursor() as cursor:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) DEFAULT NULL,
            phone VARCHAR(255) NOT NULL,
            degree TEXT NOT NULL,
            designition TEXT NOT NULL,
            skills TEXT NOT NULL
        )
    """)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_resume():
    # Get the uploaded files
    resumes = request.files.getlist('resume')
    total_resumes = len(resumes)
    parsed_resumes = 0
    chunk_size = 5 # Define the chunk size here
    
    # Chunk the resumes into smaller groups
    chunks = [resumes[i:i+chunk_size] for i in range(0, total_resumes, chunk_size)]
    num_chunks = len(chunks)
    current_chunk = 1
    
    for chunk in chunks:
        # Loop over the files and parse each one
        for resume in chunk:
            # Get the file name and extension
            filename, extension = os.path.splitext(resume.filename)
            # Add a timestamp to the file name to avoid duplicate file names
            timestamp = str(int(time.time()))
            filename = f"{filename}_{timestamp}{extension}"
            resume.save(os.path.join('./resume', filename))
            data = resumeparse.read_file(os.path.join('./resume', filename))

            # Check if the email data is present in the parsed resume
            name = data.get('name',"Not Found")
            email = data.get('email', "Not Found")
            phone = data.get('phone', "Not Found")
            degree = ",".join(data.get('degree', ["Not Found"]))
            designition = ",".join(data.get('designition', ["Not Found"]))
            skills = ",".join(data.get('skills', ["Not Found"]))

            # Insert the parsed data into the database
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO resumes (
                        name, email, phone, degree, designition, skills
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s
                    )
                """, (
                    data['name'], data['email'], data['phone'],
                    ",".join(data['degree']), ",".join(data['designition']),
                    ",".join(data['skills'])
                ))
            connection.commit()

            parsed_resumes += 1
            progress = int(parsed_resumes/total_resumes * 100)

        # Send the progress to the front-end using AJAX
        response = jsonify({'progress': progress, 'chunk': current_chunk, 'total_chunks': num_chunks})
        response.status_code = 200
        return response

        current_chunk += 1

    return 'Resumes uploaded successfully'

if __name__ == '__main__':
    app.run(debug=True)
