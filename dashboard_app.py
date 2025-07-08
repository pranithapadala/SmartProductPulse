# dashboard_app.py (Refined Version with Enhancements)

# --- 1. Imports ---
import dash
from dash import dcc, html
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os
import re
import logging
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pycountry_convert as pc
import difflib

logging.basicConfig(level=logging.INFO)

# --- 2. Utility Functions ---
def safe_read_csv(path):
    if os.path.exists(path):
        return pd.read_csv(path)
    logging.error(f"File not found: {path}")
    return pd.DataFrame()

def find_best_amazon_match(product_title, amazon_titles):
    match = difflib.get_close_matches(product_title, amazon_titles, n=1, cutoff=0.3)
    return match[0] if match else None

def get_country_code(location_text):
    if not isinstance(location_text, str): return None
    clean_loc = re.sub(r'[^a-z\s]', '', location_text.lower().strip())
    tokens = clean_loc.split()
    for token in [clean_loc] + tokens:
        if token in country_name_map:
            return country_name_map[token]
        try:
            return pc.country_name_to_country_alpha3(token.title())
        except (KeyError, TypeError):
            continue
    return None

# --- 3. Load and Prepare Data ---
def load_and_process_data():
    logging.info("Loading raw data files...")
    RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/raw")

    df_products = safe_read_csv(os.path.join(RAW_DATA_DIR, "cool_gadgets_products.csv"))
    df_reddit = safe_read_csv(os.path.join(RAW_DATA_DIR, "raw_reddit_posts.csv"))
    df_amazon = safe_read_csv(os.path.join(RAW_DATA_DIR, "Amazon products.csv"))

    logging.info("Processing sentiment analysis...")
    analyzer = SentimentIntensityAnalyzer()
    df_reddit['sentiment_score'] = df_reddit['text'].astype(str).apply(lambda t: analyzer.polarity_scores(t)['compound'])
    agg_reddit = df_reddit.groupby('product_id').agg(
        social_sentiment=('sentiment_score', 'mean'),
        social_mentions=('product_id', 'size')
    ).reset_index()

    logging.info("Matching Amazon review counts...")
    df_amazon_clean = df_amazon[['title', 'reviews_count']].copy()
    df_amazon_clean['reviews_count'] = pd.to_numeric(df_amazon_clean['reviews_count'], errors='coerce').fillna(0)
    review_data = []
    for _, product in df_products.iterrows():
        match_title = find_best_amazon_match(product['title'], df_amazon_clean['title'].tolist())
        if match_title:
            review_count = int(df_amazon_clean[df_amazon_clean['title'] == match_title]['reviews_count'].values[0])
        else:
            review_count = 0
        review_data.append({'id': product['id'], 'review_count': review_count})
    df_reviews = pd.DataFrame(review_data)

    logging.info("Combining master data table...")
    df_master = pd.merge(df_products, df_reviews, on='id', how='left')
    df_master = pd.merge(df_master, agg_reddit, left_on='id', right_on='product_id', how='left').fillna(0)
    df_master['review_count'] = df_master['review_count'].astype(int)
    df_master['social_sentiment'] = df_master['social_sentiment'].round(2)
    max_reviews = df_master['review_count'].max()
    df_master['popularity_score'] = (df_master['review_count'] / max_reviews) if max_reviews > 0 else 0

    logging.info("Processing geospatial data...")
    df_reddit_geo = df_reddit.dropna(subset=['location']).copy()
    df_reddit_geo['country_code'] = df_reddit_geo['location'].apply(get_country_code)
    country_mentions = df_reddit_geo.dropna(subset=['country_code'])['country_code'].value_counts().reset_index()
    country_mentions.columns = ['country_code', 'mention_count']

    return df_master, country_mentions

# --- 4. Build Figures ---
def create_figures(df_master, country_mentions):
    top_sentiment = df_master.loc[df_master['social_sentiment'].idxmax()]
    top_reviews = df_master.loc[df_master['review_count'].idxmax()]

    fig_bar = go.Figure([
        go.Bar(name='Social Sentiment', x=df_master['title'], y=df_master['social_sentiment']),
        go.Bar(name='Product Popularity', x=df_master['title'], y=df_master['popularity_score'])
    ])
    fig_bar.update_layout(barmode='group', title_text='Social Sentiment vs. Popularity Score', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))

    fig_scatter = px.scatter(df_master, x='social_sentiment', y='popularity_score', text='title', size='social_mentions', color='category', hover_data=['review_count'], title='Analysis Quadrant')
    fig_scatter.update_traces(textposition='top center')
    fig_scatter.add_vline(x=df_master['social_sentiment'].mean(), line_dash="dash", annotation_text="Avg Sentiment")
    fig_scatter.add_hline(y=df_master['popularity_score'].mean(), line_dash="dash", annotation_text="Avg Popularity")

    fig_map = px.choropleth(country_mentions, locations="country_code", color="mention_count", hover_name="country_code", color_continuous_scale=px.colors.sequential.Plasma, title='Global Distribution of Social Media Mentions')
    fig_map.update_layout(margin={"r":0,"t":40,"l":0,"b":0})

    return top_sentiment, top_reviews, fig_bar, fig_scatter, fig_map

# --- 5. Dashboard App Setup ---
logging.info("Initializing Dashboard App")
df_master, country_mentions = load_and_process_data()
top_sentiment_product, top_reviewed_product, fig_bar, fig_scatter, fig_map = create_figures(df_master, country_mentions)

app = dash.Dash(__name__, assets_folder='assets')
server = app.server

app.layout = html.Div(style={'backgroundColor': '#f9f9f9'}, children=[
    html.Div([
        html.H1('🚀 Smart Product Pulse Dashboard'),
        html.P('An integrated analysis of product popularity and real-time social media sentiment.')
    ], style={'padding': '20px', 'textAlign': 'center', 'backgroundColor': '#1E3A5F', 'color': 'white'}),

    html.Div([
        html.Div([
            html.Div([
                html.Div([html.H3("Most Loved Product (Social)"), html.P(top_sentiment_product['title'], style={'fontSize': 18, 'color': '#2ca02c'})], className='kpi-box'),
                html.Div([html.H3("Most Reviewed Product"), html.P(top_reviewed_product['title'], style={'fontSize': 18})], className='kpi-box'),
                html.Div([html.H3("Total Social Mentions"), html.P(f"{df_master['social_mentions'].sum():.0f}", style={'fontSize': 24})], className='kpi-box')
            ], className='kpi-container'),

            html.Div([dcc.Loading(dcc.Graph(id='bar-chart', figure=fig_bar))], className='chart-container'),

            html.Div([
                dcc.Graph(id='scatter-plot', figure=fig_scatter, className='half-width-chart'),
                dcc.Graph(id='map-chart', figure=fig_map, className='half-width-chart'),
            ], className='chart-row-container'),
        ], style={'padding': '20px'})
    ])
])

# --- 6. Run App ---
if __name__ == '__main__':
    logging.info("Starting Dashboard Server at http://127.0.0.1:8050/")
    app.run(debug=False)

# --- Country Mapping ---
country_name_map = {'usa': 'USA', 'us': 'USA', 'uk': 'GBR', 'united kingdom': 'GBR', 'ca': 'CAN'}
