from flask import Flask, render_template, request, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import calculation as report
from pptx import Presentation

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'scratch'

# Rutas de los archivos
PPTX_TEMPLATE_PATH = "powerpoints/Reporte_plantilla.pptx"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Procesar el archivo CSV
        csv_file = request.files.get('csv_file')
        wordcloud_file = request.files.get('wordcloud_file')
        
        if not csv_file:
            return "No se subió un archivo CSV.", 400

        # Guardar el archivo CSV
        csv_filename = secure_filename(csv_file.filename)
        csv_path = os.path.join(app.config['UPLOAD_FOLDER'], csv_filename)
        csv_file.save(csv_path)

        # Guardar la imagen Wordcloud, si se proporciona
        if wordcloud_file:
            wordcloud_path = os.path.join(app.config['UPLOAD_FOLDER'], 'Wordcloud.png')
            wordcloud_file.save(wordcloud_path)
        else:
            wordcloud_path = None  # Si no hay imagen, procesar con valor None
        
        # Procesar el archivo y generar el PPTX
        output_pptx_path, processed_csv_path = process_report(csv_path, wordcloud_path)

        # Redirigir a la página de descarga
        return render_template('download.html', pptx_path=output_pptx_path, csv_path=processed_csv_path)
    
    return render_template('index.html')

def process_report(csv_path, wordcloud_path):
    # Lógica de procesamiento utilizando `calculation.py`
    df_cleaned = report.load_and_clean_data(csv_path)
    df_cleaned['Influencer'] = df_cleaned.apply(report.update_influencer, axis=1)
    df_cleaned['Sentiment'] = df_cleaned.apply(report.update_sentiment, axis=1)
    
    total_mentions, count_of_authors, estimated_reach = report.calculate_summary_metrics(df_cleaned)
    report.save_cleaned_csv(df_cleaned, csv_path)  # Guardar CSV procesado
    
    report.create_mentions_evolution_chart(df_cleaned)
    report.create_sentiment_pie_chart(df_cleaned)

    # Generación de PPTX usando los valores calculados
    prs = Presentation(PPTX_TEMPLATE_PATH)
    
    # Llamadas para insertar datos en cada slide, como en `main.py`
    
    output_pptx_path = os.path.join(app.config['UPLOAD_FOLDER'], f"Reporte_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.pptx")
    prs.save(output_pptx_path)
    
    return output_pptx_path, csv_path

@app.route('/download/<path:filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)