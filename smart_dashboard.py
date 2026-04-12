import gradio as gr
import plotsense as ps
import pandas as pd
from dotenv import load_dotenv
import io
import matplotlib.pyplot as plt

# Load your Groq API key from the .env file
load_dotenv()

def process_csv(file):
    """Process uploaded CSV and generate analytics dashboard"""
    try:
        # Read the CSV file
        df = pd.read_csv(file.name)
        
        # Get dataset info
        dataset_info = f"Dataset shape: {df.shape}\n\nFirst few rows:\n{df.head().to_string()}"
        
        # Get AI Recommendations
        recommendations = ps.recommender(df, n=5)
        recommendations_text = "Top 5 Chart Recommendations:\n" + recommendations.to_string()
        
        # Generate Plot from top recommendation
        fig = ps.plotgen(df, recommendations.iloc[0])
        
        # Get AI Explanations
        explanation = ps.explainer(fig)
        
        # Combine all insights
        ai_insights = f"AI Insights:\n{explanation}"
        
        return dataset_info, fig, recommendations_text, ai_insights
    
    except Exception as e:
        return f"Error: {str(e)}", None, f"Error: {str(e)}", f"Error: {str(e)}"

# Create Gradio Interface
with gr.Blocks(title="PlotSense Dashboard Analytics") as demo:
    gr.Markdown("# 📊 PlotSense Dashboard Analytics")
    gr.Markdown("Upload a CSV file to get AI-powered analytics, visualizations, and insights")
    
    with gr.Row():
        with gr.Column(scale=1):
            csv_file = gr.File(label="📁 Upload CSV File", file_types=[".csv"])
            submit_btn = gr.Button("🚀 Generate Analytics", variant="primary")
    
    gr.Markdown("---")
    
    with gr.Row():
        with gr.Column(scale=1):
            dataset_info = gr.Textbox(label="📋 Dataset Info", lines=8, interactive=False)
        
        with gr.Column(scale=1):
            recommendations = gr.Textbox(label="📈 Chart Recommendations", lines=8, interactive=False)
    
    with gr.Row():
        plot_output = gr.Plot(label="📊 Generated Dashboard")
    
    with gr.Row():
        ai_insights = gr.Textbox(label="🤖 AI Insights", lines=6, interactive=False)
    
    # Connect the submit button
    submit_btn.click(
        fn=process_csv,
        inputs=csv_file,
        outputs=[dataset_info, plot_output, recommendations, ai_insights]
    )

if __name__ == "__main__":
    demo.launch(share=True)