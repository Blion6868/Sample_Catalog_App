from flask import Flask, render_template, request, redirect, send_file, flash, url_for
import pandas as pd
import io

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Secret key for flash messages

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def perform_audit(df):
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
                return df_to_audit.sample(frac=sample_fraction, random_state=42)

    def simple_sample(df_to_audit):
        sampling_column = determine_sampling_column(df_to_audit)
        
        if len(df_to_audit) >= 15000:
            return sample_items(df_to_audit, sampling_column, 0.05)
        elif len(df_to_audit) <= 10000:
            return sample_items(df_to_audit, sampling_column, 0.03)
        elif len(df_to_audit) <= 1500:
            return sample_items(df_to_audit, sampling_column, 0.01)
        else:
            return None

    final_sample = simple_sample(df_to_audit)

    if final_sample is not None:
        sampled_df = df[df['Retailer Item ID'].isin(final_sample['Retailer Item ID'])]
        sampled_df.loc[sampled_df['Track Item'] == 'Y', 'Track Item'] = 'Audit'  # Change 'Y' to 'Audit'
        return sampled_df

    return None  # If no sample was created

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                df = pd.read_csv(file)
            except Exception as e:
                print(f"Error reading the file: {e}")
                flash('Error processing file')
                return redirect(request.url)

            audited_data = perform_audit(df)
            if audited_data is not None:
                output = io.StringIO()
                audited_data.to_csv(output, index=False)
                output.seek(0)
                return send_file(
                    io.BytesIO(output.getvalue().encode()),
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name='audited_data.csv'
                )
            else:
                flash('No items to audit')
                return redirect(request.url)
        else:
            flash('Invalid file type')
            return redirect(request.url)
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
