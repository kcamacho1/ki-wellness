from flask import Flask, render_template, request, jsonify, session
import os
import json
import requests
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.utils
from dotenv import load_dotenv
import openai
from PIL import Image
import io
import base64
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

class AIDashboard:
    def __init__(self):
        self.sample_data = self.generate_sample_data()
        self.chat_history = []
        self.analytics_data = self.generate_analytics_data()
    
    def generate_sample_data(self):
        """Generate sample data for demonstrations"""
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
        
        data = {
            'date': dates,
            'sales': np.random.normal(1000, 200, len(dates)),
            'users': np.random.normal(500, 100, len(dates)),
            'conversion_rate': np.random.normal(0.15, 0.05, len(dates)),
            'customer_satisfaction': np.random.normal(4.2, 0.3, len(dates)),
            'ai_accuracy': np.random.normal(0.92, 0.03, len(dates)),
            'response_time': np.random.normal(1.5, 0.2, len(dates))
        }
        
        return pd.DataFrame(data)
    
    def generate_analytics_data(self):
        """Generate analytics data for AI insights"""
        np.random.seed(42)
        n_samples = 1000
        
        # Customer segments
        segments = ['High Value', 'Medium Value', 'Low Value']
        segment_data = np.random.choice(segments, n_samples, p=[0.2, 0.5, 0.3])
        
        # Purchase behavior
        purchase_amount = np.random.exponential(100, n_samples)
        purchase_frequency = np.random.poisson(3, n_samples)
        
        # AI interaction data
        ai_interactions = np.random.poisson(5, n_samples)
        ai_satisfaction = np.random.normal(4.0, 0.8, n_samples)
        
        analytics_df = pd.DataFrame({
            'customer_id': range(1, n_samples + 1),
            'segment': segment_data,
            'purchase_amount': purchase_amount,
            'purchase_frequency': purchase_frequency,
            'ai_interactions': ai_interactions,
            'ai_satisfaction': np.clip(ai_satisfaction, 1, 5)
        })
        
        return analytics_df
    
    def get_ai_insights(self, data_type):
        """Generate AI-powered insights"""
        if data_type == 'sales':
            return {
                'trend': 'increasing',
                'confidence': 0.85,
                'prediction': 'Sales expected to grow 15% next quarter',
                'key_factors': ['Seasonal demand', 'Marketing campaigns', 'Product improvements'],
                'recommendations': ['Increase marketing budget', 'Optimize pricing strategy', 'Enhance customer support']
            }
        elif data_type == 'users':
            return {
                'trend': 'stable',
                'confidence': 0.78,
                'prediction': 'User growth expected to maintain current rate',
                'key_factors': ['User retention', 'Referral program', 'Product quality'],
                'recommendations': ['Improve onboarding process', 'Launch referral incentives', 'Enhance user experience']
            }
        elif data_type == 'ai_performance':
            return {
                'trend': 'improving',
                'confidence': 0.92,
                'prediction': 'AI accuracy expected to reach 95% by end of year',
                'key_factors': ['Model updates', 'Data quality', 'Training improvements'],
                'recommendations': ['Continue model optimization', 'Expand training data', 'Implement A/B testing']
            }
        return {}
    
    def generate_chart(self, chart_type, data_type='sales'):
        """Generate interactive charts using Plotly"""
        if chart_type == 'line':
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=self.sample_data['date'],
                y=self.sample_data[data_type],
                mode='lines+markers',
                name=data_type.replace('_', ' ').title(),
                line=dict(color='#3B82F6', width=3)
            ))
            fig.update_layout(
                title=f'{data_type.replace("_", " ").title()} Over Time',
                xaxis_title='Date',
                yaxis_title=data_type.replace('_', ' ').title(),
                template='plotly_white',
                height=400
            )
            return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        elif chart_type == 'bar':
            monthly_data = self.sample_data.groupby(self.sample_data['date'].dt.to_period('M'))[data_type].mean()
            fig = go.Figure(data=[
                go.Bar(
                    x=[str(x) for x in monthly_data.index],
                    y=monthly_data.values,
                    marker_color='#10B981'
                )
            ])
            fig.update_layout(
                title=f'Monthly Average {data_type.replace("_", " ").title()}',
                xaxis_title='Month',
                yaxis_title=data_type.replace('_', ' ').title(),
                template='plotly_white',
                height=400
            )
            return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        elif chart_type == 'scatter':
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=self.sample_data['sales'],
                y=self.sample_data['users'],
                mode='markers',
                marker=dict(
                    size=10,
                    color=self.sample_data['conversion_rate'],
                    colorscale='Viridis',
                    showscale=True
                ),
                text=self.sample_data['date'].dt.strftime('%Y-%m-%d'),
                hovertemplate='<b>Date:</b> %{text}<br><b>Sales:</b> %{x}<br><b>Users:</b> %{y}<br><b>Conversion:</b> %{marker.color:.3f}<extra></extra>'
            ))
            fig.update_layout(
                title='Sales vs Users (Color: Conversion Rate)',
                xaxis_title='Sales',
                yaxis_title='Users',
                template='plotly_white',
                height=400
            )
            return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        elif chart_type == 'heatmap':
            # Create correlation matrix
            numeric_cols = ['sales', 'users', 'conversion_rate', 'customer_satisfaction', 'ai_accuracy', 'response_time']
            corr_matrix = self.sample_data[numeric_cols].corr()
            
            fig = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=corr_matrix.columns,
                y=corr_matrix.columns,
                colorscale='RdBu',
                zmid=0
            ))
            fig.update_layout(
                title='Feature Correlation Matrix',
                template='plotly_white',
                height=400
            )
            return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        return None
    
    def get_customer_segments(self):
        """Generate customer segmentation analysis"""
        # Perform K-means clustering
        features = ['purchase_amount', 'purchase_frequency', 'ai_interactions', 'ai_satisfaction']
        X = self.analytics_data[features].values
        
        # Standardize features
        X = (X - X.mean(axis=0)) / X.std(axis=0)
        
        # Perform clustering
        kmeans = KMeans(n_clusters=4, random_state=42)
        clusters = kmeans.fit_predict(X)
        
        # Add cluster labels
        self.analytics_data['cluster'] = clusters
        
        # Analyze clusters
        cluster_analysis = {}
        for cluster_id in range(4):
            cluster_data = self.analytics_data[self.analytics_data['cluster'] == cluster_id]
            cluster_analysis[f'Cluster {cluster_id + 1}'] = {
                'size': len(cluster_data),
                'avg_purchase': cluster_data['purchase_amount'].mean(),
                'avg_frequency': cluster_data['purchase_frequency'].mean(),
                'avg_ai_interactions': cluster_data['ai_interactions'].mean(),
                'avg_satisfaction': cluster_data['ai_satisfaction'].mean()
            }
        
        return cluster_analysis
    
    def chat_with_ai(self, message):
        """Chat with AI assistant"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI assistant for a business analytics dashboard. Provide helpful insights and recommendations based on data analysis."},
                    {"role": "user", "content": message}
                ],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Sorry, I couldn't process your request. Error: {str(e)}"

# Initialize dashboard
dashboard = AIDashboard()

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/chart/<chart_type>')
def get_chart(chart_type):
    """API endpoint to get chart data"""
    data_type = request.args.get('data_type', 'sales')
    chart_data = dashboard.generate_chart(chart_type, data_type)
    return jsonify({'chart_data': chart_data})

@app.route('/api/insights/<data_type>')
def get_insights(data_type):
    """API endpoint to get AI insights"""
    insights = dashboard.get_ai_insights(data_type)
    return jsonify(insights)

@app.route('/api/segments')
def get_segments():
    """API endpoint to get customer segments"""
    segments = dashboard.get_customer_segments()
    return jsonify(segments)

@app.route('/api/chat', methods=['POST'])
def chat():
    """API endpoint for AI chat"""
    data = request.get_json()
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    response = dashboard.chat_with_ai(message)
    return jsonify({'response': response})

@app.route('/api/stats')
def get_stats():
    """API endpoint to get dashboard statistics"""
    stats = {
        'total_sales': int(dashboard.sample_data['sales'].sum()),
        'total_users': int(dashboard.sample_data['users'].sum()),
        'avg_conversion': round(dashboard.sample_data['conversion_rate'].mean() * 100, 2),
        'avg_satisfaction': round(dashboard.sample_data['customer_satisfaction'].mean(), 2),
        'ai_accuracy': round(dashboard.sample_data['ai_accuracy'].mean() * 100, 2),
        'avg_response_time': round(dashboard.sample_data['response_time'].mean(), 2)
    }
    return jsonify(stats)

@app.route('/predictions')
def predictions():
    """Predictions page"""
    return render_template('predictions.html')

@app.route('/analytics')
def analytics():
    """Analytics page"""
    return render_template('analytics.html')

@app.route('/ai-chat')
def ai_chat():
    """AI Chat page"""
    return render_template('ai_chat.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 