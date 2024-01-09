from flask import Flask, render_template, request, send_file
import pandas as pd
import tkinter as tk
from tkinter import filedialog
import io

app = Flask(__name__)

def read_and_sample(file_path):
    try:
        with open(file_path, 'rb') as file:
            content = file.read()
            df = pd.read_csv(io.StringIO(content.decode('utf-8', errors='replace')))
    except Exception as e:
        print(f"Error reading the file: {e}")
        return None
    df_to_audit = df[df['Track Item'] == 'Y']

    def determine_sampling_column(df_to_audit):
        if df_to_audit['Subcategory'].isnull().all():
            sampling_column = 'Subcategory'
        else:
            sampling_column = 'Category'
        return sampling_column

    def sample_items(df_to_audit, sampling_column, sample_fraction):
        if len(df_to_audit) == 0:
            return None
        else:
            return df_to_audit.groupby(sampling_column).apply(lambda x: x.sample(frac=sample_fraction, random_state=42) if len(x) * sample_fraction >= 2 else x.sample(n=2, random_state=42))

    def simple_sample(df_to_audit):
        sampling_column = determine_sampling_column(df_to_audit)
        if len(df_to_audit) >= 15000:
            return sample_items(df_to_audit, sampling_column, 0.05)
        elif len(df_to_audit) >= 10000:
            return sample_items(df_to_audit, sampling_column, 0.03)
        elif len(df_to_audit) >= 1500:
            return sample_items(df_to_audit, sampling_column, 0.01)
        else:
            return None

    final_sample = simple_sample(df_to_audit)
    if final_sample is None:
        return "No data to sample or error occurred."
    df.loc[df['Retailer Item ID'].isin(final_sample['Retailer Item ID']), 'Track Item'] = 'Audit'
    df.to_csv('Catalog_Audit.csv', index=False)
    return 'Catalog_Audit.csv'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file.filename != '':
            file_path = 'uploads/' + uploaded_file.filename
            uploaded_file.save(file_path)
            result = read_and_sample(file_path)
            if result != "No data to sample or error occurred.":
                return send_file(result, as_attachment=True)
            else:
                return result
    return render_template('upload.html')

if __name__ == '__main__':
    app.run(debug=True)
