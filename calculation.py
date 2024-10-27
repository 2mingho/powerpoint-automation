# Imports de las librerías necesarias
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import textwrap
import os

# Definición de las constantes y configuraciones
social_networks_prensa = ['@EdeesteRD', '@edeesterd', "edenorterd", "edesurrd", '@precisionportal', 'panoramatv_', '@mananerord', '@noticiaspimentl', '@MIC_RD', "siegobrd", '@soldelamananard', '@drmariolama', '@labazucaenlared', '@eldia_do', '@diariosaluddo', '@noticiasrnn', '@periodicohoy', '@telemicrohd', '@precisionportal', '@telenoticiasrd', '@sin24horas', 'sin24horas', '@diariolibre', 'diariolibre', '@cdn37', 'cdn.com.do', '@listindiario', 'listindiario', 'bavaronews', '@acentodiario', '@anoticias7', '@z101digital', 'z101digital', 'revista110', 'rcavada', '@rcavada', 'robertocavada', 'ndigital', 'bavarodigital', '@elnuevodiariord', '@acentodiario', '@deultimominutomedia', '@aeromundo_ggomez', '@cachichatv', '@remolachanews', '@ntelemicro5', '@megadiariord', '@noticiasmn', '@eldemocratard', '@elpregonerord', '@infoturdom', '@comunidadojala', '@panorama_do', '@panoramard1', '@invertix', '@derechoasaberlo', '@rccmediard', '@n16noticias', '@lospueblistas']

social_network_sources = {
    'Twitter': 'Redes Sociales',
    'Youtube': 'Redes Sociales',
    'Instagram': 'Redes Sociales',
    'Facebook': 'Redes Sociales',
    'Pinterest': 'Redes Sociales',
    'Reddit': 'Redes Sociales',
    'TikTok': 'Redes Sociales',
    'Twitch': 'Redes Sociales',
}

# Función para formatear el alcance
def format_number(number):
    """Format a number to display in millions (M) or thousands (k)"""
    if number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    elif number >= 1_000:
        return f"{number / 1_000:.1f}k"
    return str(number)

# Función para cargar y limpiar el DataFrame
def load_and_clean_data(file_path):
    df = pd.read_csv(file_path, encoding='utf-16', sep='\t')
    columns_to_delete = [
        'Opening Text', 'Subregion', 'Desktop Reach', 'Mobile Reach',
        'Twitter Social Echo', 'Facebook Social Echo', 'Reddit Social Echo',
        'National Viewership', 'AVE', 'State', 'City',
        'Social Echo Total', 'Editorial Echo', 'Views', 'Estimated Views',
        'Likes', 'Replies', 'Retweets', 'Comments', 'Shares', 'Reactions',
        'Threads', 'Is Verified'
    ]
    df_cleaned = df.drop(columns=columns_to_delete, errors='ignore')
    df_cleaned['Hit Sentence'] = df_cleaned['Headline'].where(~df_cleaned['Headline'].isna(), df_cleaned['Hit Sentence'])
    exclude_sources = ['Blogs', 'Twitter', 'Youtube', 'Instagram', 'Facebook', 'Pinterest', 'Reddit', 'TikTok', 'Twitch']
    mask = ~df_cleaned['Source'].isin(exclude_sources)
    df_cleaned.loc[mask, 'Influencer'] = df_cleaned.loc[mask, 'Source']
    df_cleaned['Plataforma'] = df_cleaned['Source'].apply(lambda x: social_network_sources.get(x, 'Prensa Digital'))
    return df_cleaned

# Función para actualizar la columna 'Influencer' para comentarios en Facebook
def update_influencer(row):
    if row['Source'] == 'Facebook' and row['Reach'] == 0:
        return "Comment on " + row['Influencer']
    return row['Influencer']

# Función para actualizar el sentimiento
def update_sentiment(df):
    df['Sentiment'] = df['Sentiment'].apply(lambda x: "Neutral" if x == "Unknown" or pd.isna(x) else x)
    mask = (df['Influencer'].isin(social_networks_prensa)) | (df['Plataforma'] == 'Prensa Digital') | (df['Source'] == 'Youtube')
    df['Sentiment'] = np.where(mask, "Neutral", df['Sentiment'].where(df['Sentiment'].isin(["Positive", "Negative", "Neutral"]), "Neutral"))
    return df

# Función para calcular métricas de resumen
def calculate_summary_metrics(df):
    total_mentions = len(df)
    count_of_authors = df['Influencer'].nunique()
    estimated_reach = df.groupby('Influencer')['Reach'].max().sum()
    formatted_estimated_reach = format_number(estimated_reach)
    return total_mentions, count_of_authors, formatted_estimated_reach

# Función para generar gráfico de evolución temporal de menciones
def create_mentions_evolution_chart(df, date_column='Alternate Date Format', time_column='Time', output_path='scratch/convEvolution.png'):
    df['date'] = pd.to_datetime(df[date_column], format='%d-%b-%y').dt.date
    df['hour'] = pd.to_datetime(df[time_column], format='%I:%M %p').dt.strftime('%I %p')
    df_grouped = df.groupby(['date', 'hour']).size().reset_index(name='count')
    df_grouped['datetime'] = pd.to_datetime(df_grouped['date'].astype(str) + ' ' + df_grouped['hour'])
    df_grouped = df_grouped.sort_values('datetime')
    
    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(df_grouped['datetime'], df_grouped['count'], linewidth=2, color='steelblue')
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b %I %p'))
    plt.xticks(rotation=45, ha='right')
    ax.set_xlabel('Fecha y Hora')
    ax.set_ylabel('Cantidad de Menciones')
    ax.set_title('Evolución de Menciones por Hora')
    plt.tight_layout()
    plt.savefig(output_path, transparent=True)

# Función para generar gráfico de pie de sentimientos
def create_sentiment_pie_chart(df, output_path='scratch/sentiment_pie_chart.png'):
    sentiment_counts = df[df['Sentiment'] != 'Not Rated']['Sentiment'].value_counts()
    sentiment_colors = {'Negative': '#ff0000', 'Positive': '#00b050', 'Neutral': '#BFBFBF'}
    labels = sentiment_counts.index.to_list()
    sizes = sentiment_counts.to_list()
    
    plt.figure(figsize=(10, 10))
    colors = [sentiment_colors.get(label, 'lightgray') for label in labels]
    plt.pie(sizes, autopct="%1.1f%%", colors=colors, textprops=dict(backgroundcolor='w', fontsize=14, fontweight='bold'), startangle=140)
    plt.axis('equal')
    plt.savefig(output_path, transparent=True)

# Función para distribución por plataforma
def distribucion_plataforma(df):
    platform_counts = df['Plataforma'].value_counts()
    max_reach_per_platform = df.groupby('Plataforma')['Reach'].max().apply(format_number)
    return platform_counts.to_dict(), max_reach_per_platform.to_dict()

# Función para extraer las 5 'Hit Sentence' principales
def get_top_5_hit_sentences(df):
    top_influencers = df[df['Plataforma'] == "Prensa Digital"].sort_values(by=['Reach'], ascending=False).head(5)['Hit Sentence']
    return [textwrap.fill(sentence, width=100) for sentence in top_influencers]

# Función para guardar el dataframe modificado como archivo csv
def save_cleaned_csv(df, file_path):
    base_filename = os.path.basename(file_path).split()[0]
    base_filename = base_filename.split('.')[0]
    output_filename = f"{base_filename}_(resultado).csv"
    with open(output_filename, 'w', encoding='utf-16', newline='') as f:
        df.to_csv(f, index=False, sep='\t')
    print(f"CSV data saved to: {output_filename}")