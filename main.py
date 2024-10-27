import os
from pptx import Presentation
from pptx.util import Inches
from datetime import datetime
import calculation as report

# Variables y rutas de archivo
file_path = "scratch/MTRABAJO - Oct 14, 2024 - 12 01 11 PM.csv"
pptx_template_path = "powerpoints/Reporte_plantilla.pptx"

# Cargar y limpiar datos
df = report.load_data(file_path)
df_cleaned = report.clean_data(df)
df_cleaned = report.filtrar_sentimientos(df_cleaned)

# Obtener métricas
total_mentions, count_of_authors, estimated_reach = report.calculate_metrics(df_cleaned)
formatted_estimated_reach = report.format_number(estimated_reach)

# Guardar datos limpios
report.save_cleaned_data(df_cleaned, file_path)

# Crear gráficos
# report.plot_by_date_or_hour(df_cleaned, use_hours=True)
report.plot_sentiment_distribution(df_cleaned)

# Preparar nombre del archivo y cliente
current_date = datetime.now().strftime('%d-%b-%Y')
client_name = os.path.basename(file_path).split()[0]

# Cargar presentación y modificar slides
prs = Presentation(pptx_template_path)
slides_info = [
    {'slide_num': 0, 'replace_dict': {"REPORT_CLIENT": client_name, "REPORT_DATE": current_date}},
    {'slide_num': 1, 'replace_dict': {"NUMB_MENTIONS": str(total_mentions), "NUMB_ACTORS": str(count_of_authors), "EST_REACH": formatted_estimated_reach}},
    {'slide_num': 2, 'replace_dict': {"TOP_NEWS": "\n".join(df_cleaned['Hit Sentence'].head(5))}},
    {'slide_num': 3, 'replace_dict': {}, 'image': 'sentiment_pie_chart.png'}
]

for slide_info in slides_info:
    slide = prs.slides[slide_info['slide_num']]
    for shape in slide.shapes:
        if shape.has_text_frame:
            for key, value in slide_info['replace_dict'].items():
                if key in shape.text:
                    shape.text = value
        if 'image' in slide_info and shape.shape_type == 13:
            slide.shapes.add_picture(slide_info['image'], Inches(1), Inches(1), width=Inches(4), height=Inches(4))

# Guardar presentación con el nombre de "REPORT_CLIENT"
output_filename = f"{client_name} {current_date}.pptx"
prs.save(output_filename)
print(f"Presentación guardada como {output_filename}")
