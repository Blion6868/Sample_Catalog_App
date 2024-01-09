from flask import Flask, render_template, request, redirect, url_for
from flask import send_file, flash
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Secret key for flash messages

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def perform_audit(file):
    try:
        df = pd.read_csv(file)
    except Exception as e:
        return f"Error reading the file: {e}"

    df_to_audit = df[df['Track Item'] == 'Y']

    def determine_sampling_column(df_to_audit):
        if df_to_audit['Subcategory'].isnull().all():
            return 'Subcategory'
        else:
            return 'Category'

    def sample_items(df_to_audit, sampling_column, sample_fraction):
        if len(df_to_audit) == 0:
            return None
        else:
            return df_to_audit.groupby(sampling_column).apply(lambda x: x.sample(frac=sample_fraction, random_state=42) if len(x) * sample_fraction >= 2 else x.sample(n=2, random_state=42))

    def simple_sample(df_to_audit):
        print(f"Length of df_to_audit: {len(df_to_audit)}")  # Debugging line to check the length of df_to_audit

        sampling_column = determine_sampling_column(df_to_audit)
        print(f"Sampling Column: {sampling_column}")  # Debugging line to check the sampling column

        if len(df_to_audit) >= 15000:
            print("Applying 5% sampling")
            return sample_items(df_to_audit, sampling_column, 0.05)
        elif len(df_to_audit) >= 10000:
            print("Applying 3% sampling")
            return sample_items(df_to_audit, sampling_column, 0.03)
        elif len(df_to_audit) >= 1500:
            print("Applying 1% sampling")
            return sample_items(df_to_audit, sampling_column, 0.01)
        else:
            print("No sampling")
            return None

    final_sample = simple_sample(df_to_audit)

    if final_sample is not None:
        df.loc[df['Retailer Item ID'].isin(final_sample['Retailer Item ID']), 'Track Item'] = 'Audit'

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'Catalog_Audit.csv')
    print(f"File path: {file_path}")  # Debugging line to check the file path

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        try:
            os.makedirs(app.config['UPLOAD_FOLDER'])
        except OSError as e:
            print(f"Error creating directory: {e}")
            # Handle the directory creation error here if needed

    try:
        df.to_csv(file_path, index=False)
        print("File created successfully")  # Debugging line to check if the file is created
    except Exception as e:
        print(f"Error writing the file: {e}")  # Debugging line for file writing errors

    return file_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        file_path = perform_audit(file)
        if file_path:
            return send_file(file_path, as_attachment=True)
        else:
            flash('Error processing file')
            return redirect(request.url)
    else:
        flash('Invalid file type')
        return redirect(request.url)

if __name__ == '__main__':
    app.run(debug=True)
