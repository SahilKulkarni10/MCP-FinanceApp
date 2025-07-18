from flask import Flask, render_template, request, jsonify
import os
import json
from mcp_data_service import MCPDataService
from gemini_finance_agent import GeminiFinanceAgent
from dotenv import load_dotenv
import plotly
import plotly.express as px
import pandas as pd
from datetime import datetime
import base64

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, static_folder="static")

# Initialize MCP data service
mcp_service = MCPDataService()

# Initialize Gemini agent
gemini_agent = None
try:
    gemini_agent = GeminiFinanceAgent(mcp_service)
except Exception as e:
    print(f"Error initializing Gemini agent: {str(e)}")

@app.route('/')
def index():
    """Render the home page"""
    # Get user information
    user_info = mcp_service.get_user_info()
    # Get financial summary
    financial_summary = {
        "bank_balance": mcp_service.get_total_bank_balance(),
        "net_worth": mcp_service.get_net_worth()["net_worth"],
        "total_investments": (mcp_service.get_total_mutual_fund_value() + 
                            mcp_service.get_total_stock_value()),
        "total_debt": mcp_service.get_total_loan_outstanding() + mcp_service.get_total_credit_card_debt(),
        "credit_score": mcp_service.get_credit_score()["score"]
    }
    
    # Generate a simple net worth chart for the dashboard
    net_worth_history = mcp_service.get_net_worth_history()
    dates = [entry["date"] for entry in net_worth_history]
    values = [entry["net_worth"] for entry in net_worth_history]
    
    # Create a simple Plotly figure
    df = pd.DataFrame({
        'date': dates,
        'net_worth': values
    })
    
    fig = px.line(df, x='date', y='net_worth', 
                 title='Net Worth Trend',
                 template='plotly_white')
    
    fig.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        height=200,
        xaxis_title='',
        yaxis_title='',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)'
    )
    
    # Convert the figure to JSON for embedding in the template
    net_worth_chart = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    # Get recent transactions
    recent_transactions = mcp_service.get_recent_transactions()
    
    # Get recommendations
    recommendations = mcp_service.get_recommendations()
    
    return render_template('index.html', 
                           user_info=user_info, 
                           financial_summary=financial_summary,
                           net_worth_chart=net_worth_chart,
                           recent_transactions=recent_transactions,
                           recommendations=recommendations)

@app.route('/chat', methods=['POST'])
def chat():
    """Process a chat query"""
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    if not gemini_agent:
        return jsonify({"error": "Gemini agent not initialized. Please check your API key."}), 500
    
    try:
        # Process the query
        response = gemini_agent.process_query(query)
        
        # Check if we need to generate a visualization
        chart_data, chart_type = gemini_agent.get_visualization_for_query(query)
        
        result = {
            "response": response,
            "has_visualization": chart_data is not None,
            "chart_type": chart_type
        }
        
        if chart_data:
            result["chart_data"] = chart_data
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/insights/<insight_type>')
def get_insight(insight_type):
    """Get specific financial insight"""
    if not gemini_agent:
        return jsonify({"error": "Gemini agent not initialized. Please check your API key."}), 500
    
    try:
        insight = gemini_agent.generate_insight(insight_type)
        return jsonify(insight)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/data/<data_type>')
def get_data(data_type):
    """Get specific financial data"""
    try:
        if data_type == "user_info":
            return jsonify(mcp_service.get_user_info())
        elif data_type == "bank_accounts":
            return jsonify(mcp_service.get_bank_accounts())
        elif data_type == "investments":
            return jsonify(mcp_service.get_investments())
        elif data_type == "loans":
            return jsonify(mcp_service.get_loans())
        elif data_type == "credit_score":
            return jsonify(mcp_service.get_credit_score())
        elif data_type == "spending":
            return jsonify(mcp_service.get_spending_summary())
        elif data_type == "goals":
            return jsonify(mcp_service.get_financial_goals())
        elif data_type == "net_worth":
            return jsonify(mcp_service.get_net_worth())
        elif data_type == "recommendations":
            return jsonify(mcp_service.get_recommendations())
        elif data_type == "all":
            # Get all data (for export)
            with open('mcp_data.json', 'r') as file:
                all_data = json.load(file)
            return jsonify(all_data)
        else:
            return jsonify({"error": f"Unknown data type: {data_type}"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Check if GEMINI_API_KEY is set
    if not os.getenv("GEMINI_API_KEY"):
        print("Warning: GEMINI_API_KEY environment variable not set.")
        print("Please set it in a .env file or export it as an environment variable.")
        print("The application will run but AI features (Gemini 2.0 Flash) will not work.")
    
    # Create templates and static folders if they don't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Run the Flask app
    app.run(debug=True, port=5000)
