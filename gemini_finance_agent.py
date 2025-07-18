import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from PIL import Image
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

# Load environment variables from .env file
load_dotenv()

class GeminiFinanceAgent:
    """AI agent powered by Google Gemini to provide financial insights"""
    
    def __init__(self, mcp_service):
        """Initialize the Gemini Finance Agent"""
        self.mcp_service = mcp_service
        api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set. Please set it in a .env file.")
        
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        
        # Get the Gemini Flash model
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Create a conversation history
        self.chat = self.model.start_chat(history=[])
        
        # Initialize the agent with user data and context
        self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize the agent with financial data context"""
        user_info = self.mcp_service.get_user_info()
        net_worth = self.mcp_service.get_net_worth()
        
        system_prompt = f"""
        You are Fi Money's AI Finance Assistant, an expert financial advisor who has access to {user_info['name']}'s complete financial data through Fi Money's MCP (Model Context Protocol) server.
        
        Your primary responsibility is to provide personalized financial insights, answer financial questions, analyze trends, suggest actions, simulate scenarios, and visualize outcomes based on the user's financial data.
        
        Always base your responses on the actual financial data you have access to. Be specific and tailor your advice to the user's unique financial situation. 
        
        When suggesting financial actions, consider:
        1. The user's risk profile: {user_info['risk_profile']}
        2. Current net worth: ₹{net_worth['net_worth']:,.2f}
        3. Financial goals and timeline
        4. Existing debt obligations
        5. Investment portfolio composition
        6. Income and spending patterns
        
        When generating visualizations, make them clear, informative, and visually appealing.
        
        Always maintain a professional and helpful tone. If asked to project scenarios, make clear what assumptions you're making. If asked about topics beyond the user's financial data, politely refocus the conversation on their financial situation.
        
        Remember, you are a financial advisor helping the user understand and improve their financial health using their actual personal financial data.
        """
        
        # Initialize the chat with system prompt
        response = self.chat.send_message(system_prompt)
    
    def get_financial_data_summary(self):
        """Get a summary of the user's financial data"""
        user_info = self.mcp_service.get_user_info()
        net_worth = self.mcp_service.get_net_worth()
        bank_balance = self.mcp_service.get_total_bank_balance()
        investments = self.mcp_service.get_investments()
        loans = self.mcp_service.get_loans()
        credit_score = self.mcp_service.get_credit_score()
        
        data_summary = {
            "user_info": user_info,
            "net_worth": net_worth,
            "bank_balance": bank_balance,
            "investments_summary": {
                "mutual_funds_value": self.mcp_service.get_total_mutual_fund_value(),
                "stocks_value": self.mcp_service.get_total_stock_value(),
                "epf_balance": investments.get("epf", {}).get("balance", 0),
                "ppf_balance": investments.get("ppf", {}).get("balance", 0)
            },
            "loans_summary": {
                "home_loan": loans.get("home_loan", {}).get("outstanding_amount", 0),
                "personal_loan": loans.get("personal_loan", {}).get("outstanding_amount", 0)
            },
            "credit_score": credit_score.get("score", 0)
        }
        
        return data_summary
    
    def generate_insight(self, insight_type):
        """Generate specific financial insight"""
        if insight_type == "net_worth_trend":
            return self._analyze_net_worth_trend()
        elif insight_type == "investment_performance":
            return self._analyze_investment_performance()
        elif insight_type == "spending_patterns":
            return self._analyze_spending_patterns()
        elif insight_type == "debt_analysis":
            return self._analyze_debt()
        else:
            return "Insight type not recognized."
    
    def _analyze_net_worth_trend(self):
        """Analyze net worth trend over time"""
        net_worth_history = self.mcp_service.get_net_worth_history()
        
        # Prepare data for the chart
        dates = [entry["date"] for entry in net_worth_history]
        values = [entry["net_worth"] for entry in net_worth_history]
        
        # Create a DataFrame
        df = pd.DataFrame({
            'date': dates,
            'net_worth': values
        })
        
        # Create a plotly figure
        fig = px.line(df, x='date', y='net_worth', 
                      title='Net Worth Trend',
                      labels={'date': 'Date', 'net_worth': 'Net Worth (₹)'},
                      template='plotly_white')
        
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Net Worth (₹)',
            yaxis_tickformat=',.0f'
        )
        
        # Convert to JSON for returning
        chart_json = fig.to_json()
        
        # Calculate trend metrics
        first_value = values[-1] if values else 0
        last_value = values[0] if values else 0
        change_value = last_value - first_value
        change_percent = (change_value / abs(first_value)) * 100 if first_value != 0 else 0
        
        # Determine trend direction
        if change_value > 0:
            trend = "positive"
        elif change_value < 0:
            trend = "negative"
        else:
            trend = "neutral"
        
        result = {
            "chart": chart_json,
            "metrics": {
                "current_net_worth": last_value,
                "change_value": change_value,
                "change_percent": change_percent,
                "trend": trend,
                "time_period": f"{net_worth_history[-1]['date']} to {net_worth_history[0]['date']}" if net_worth_history else "N/A"
            }
        }
        
        return result
    
    def _analyze_investment_performance(self):
        """Analyze investment performance"""
        mutual_funds = self.mcp_service.get_mutual_funds()
        stocks = self.mcp_service.get_stocks()
        
        # Prepare mutual funds data
        mf_names = [fund["name"] for fund in mutual_funds]
        mf_returns_1y = [fund["returns"]["1y"] for fund in mutual_funds]
        mf_current_values = [fund["current_value"] for fund in mutual_funds]
        
        # Prepare stocks data
        stock_names = [stock["name"] for stock in stocks]
        stock_returns = [stock["profit_loss_percentage"] for stock in stocks]
        stock_current_values = [stock["current_value"] for stock in stocks]
        
        # Create performance chart for mutual funds
        if mutual_funds:
            mf_df = pd.DataFrame({
                'name': mf_names,
                'returns_1y': mf_returns_1y,
                'current_value': mf_current_values
            })
            
            mf_fig = px.bar(mf_df, x='name', y='returns_1y', 
                         title='Mutual Fund 1-Year Returns',
                         text='returns_1y',
                         color='returns_1y',
                         color_continuous_scale=['red', 'yellow', 'green'],
                         range_color=[-5, 20])
            
            mf_fig.update_layout(
                xaxis_title='Fund Name',
                yaxis_title='1-Year Returns (%)',
                coloraxis_showscale=False
            )
            
            mf_fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            
            mf_chart_json = mf_fig.to_json()
        else:
            mf_chart_json = None
        
        # Create performance chart for stocks
        if stocks:
            stock_df = pd.DataFrame({
                'name': stock_names,
                'returns': stock_returns,
                'current_value': stock_current_values
            })
            
            stock_fig = px.bar(stock_df, x='name', y='returns', 
                            title='Stock Returns',
                            text='returns',
                            color='returns',
                            color_continuous_scale=['red', 'yellow', 'green'],
                            range_color=[-10, 30])
            
            stock_fig.update_layout(
                xaxis_title='Stock Name',
                yaxis_title='Returns (%)',
                coloraxis_showscale=False
            )
            
            stock_fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            
            stock_chart_json = stock_fig.to_json()
        else:
            stock_chart_json = None
        
        # Create portfolio allocation chart
        total_mf = sum(mf_current_values) if mf_current_values else 0
        total_stocks = sum(stock_current_values) if stock_current_values else 0
        epf_balance = self.mcp_service.get_investments().get("epf", {}).get("balance", 0)
        ppf_balance = self.mcp_service.get_investments().get("ppf", {}).get("balance", 0)
        fd_balance = sum(fd["current_value"] for fd in self.mcp_service.get_investments().get("fixed_deposits", []))
        
        portfolio_df = pd.DataFrame({
            'category': ['Mutual Funds', 'Stocks', 'EPF', 'PPF', 'Fixed Deposits'],
            'value': [total_mf, total_stocks, epf_balance, ppf_balance, fd_balance]
        })
        
        portfolio_fig = px.pie(portfolio_df, values='value', names='category', 
                            title='Investment Portfolio Allocation',
                            hole=0.4)
        
        portfolio_fig.update_traces(textposition='inside', textinfo='percent+label')
        
        portfolio_chart_json = portfolio_fig.to_json()
        
        # Calculate performance metrics
        total_investment_value = total_mf + total_stocks + epf_balance + ppf_balance + fd_balance
        weighted_return = 0
        
        if total_investment_value > 0:
            for fund in mutual_funds:
                weight = fund["current_value"] / total_investment_value
                weighted_return += fund["returns"]["1y"] * weight
            
            for stock in stocks:
                weight = stock["current_value"] / total_investment_value
                weighted_return += stock["profit_loss_percentage"] * weight
            
            # Add estimated returns for EPF, PPF, and FDs
            if epf_balance > 0:
                epf_weight = epf_balance / total_investment_value
                epf_return = self.mcp_service.get_investments().get("epf", {}).get("interest_rate", 8.15)
                weighted_return += epf_return * epf_weight
            
            if ppf_balance > 0:
                ppf_weight = ppf_balance / total_investment_value
                ppf_return = self.mcp_service.get_investments().get("ppf", {}).get("interest_rate", 7.1)
                weighted_return += ppf_return * ppf_weight
            
            if fd_balance > 0:
                fd_weight = fd_balance / total_investment_value
                # Average FD return
                fd_returns = [fd["interest_rate"] for fd in self.mcp_service.get_investments().get("fixed_deposits", [])]
                avg_fd_return = sum(fd_returns) / len(fd_returns) if fd_returns else 6.0
                weighted_return += avg_fd_return * fd_weight
        
        result = {
            "mutual_funds_chart": mf_chart_json,
            "stocks_chart": stock_chart_json,
            "portfolio_allocation_chart": portfolio_chart_json,
            "metrics": {
                "total_investment_value": total_investment_value,
                "weighted_average_return": weighted_return,
                "best_performing_asset": self._get_best_performing_asset(mutual_funds, stocks),
                "worst_performing_asset": self._get_worst_performing_asset(mutual_funds, stocks)
            }
        }
        
        return result
    
    def _get_best_performing_asset(self, mutual_funds, stocks):
        """Get the best performing asset"""
        best_mf = None
        best_mf_return = -float('inf')
        
        for fund in mutual_funds:
            if fund["returns"]["1y"] > best_mf_return:
                best_mf = fund
                best_mf_return = fund["returns"]["1y"]
        
        best_stock = None
        best_stock_return = -float('inf')
        
        for stock in stocks:
            if stock["profit_loss_percentage"] > best_stock_return:
                best_stock = stock
                best_stock_return = stock["profit_loss_percentage"]
        
        if best_mf and best_stock:
            if best_mf_return > best_stock_return:
                return {
                    "type": "Mutual Fund",
                    "name": best_mf["name"],
                    "return": best_mf_return
                }
            else:
                return {
                    "type": "Stock",
                    "name": best_stock["name"],
                    "return": best_stock_return
                }
        elif best_mf:
            return {
                "type": "Mutual Fund",
                "name": best_mf["name"],
                "return": best_mf_return
            }
        elif best_stock:
            return {
                "type": "Stock",
                "name": best_stock["name"],
                "return": best_stock_return
            }
        else:
            return None
    
    def _get_worst_performing_asset(self, mutual_funds, stocks):
        """Get the worst performing asset"""
        worst_mf = None
        worst_mf_return = float('inf')
        
        for fund in mutual_funds:
            if fund["returns"]["1y"] < worst_mf_return:
                worst_mf = fund
                worst_mf_return = fund["returns"]["1y"]
        
        worst_stock = None
        worst_stock_return = float('inf')
        
        for stock in stocks:
            if stock["profit_loss_percentage"] < worst_stock_return:
                worst_stock = stock
                worst_stock_return = stock["profit_loss_percentage"]
        
        if worst_mf and worst_stock:
            if worst_mf_return < worst_stock_return:
                return {
                    "type": "Mutual Fund",
                    "name": worst_mf["name"],
                    "return": worst_mf_return
                }
            else:
                return {
                    "type": "Stock",
                    "name": worst_stock["name"],
                    "return": worst_stock_return
                }
        elif worst_mf:
            return {
                "type": "Mutual Fund",
                "name": worst_mf["name"],
                "return": worst_mf_return
            }
        elif worst_stock:
            return {
                "type": "Stock",
                "name": worst_stock["name"],
                "return": worst_stock_return
            }
        else:
            return None
    
    def _analyze_spending_patterns(self):
        """Analyze spending patterns"""
        monthly_spending = self.mcp_service.get_monthly_spending()
        
        if not monthly_spending or "categories" not in monthly_spending:
            return "No spending data available."
        
        # Prepare data for the chart
        categories = list(monthly_spending["categories"].keys())
        amounts = list(monthly_spending["categories"].values())
        
        # Create a DataFrame
        df = pd.DataFrame({
            'category': categories,
            'amount': amounts
        })
        
        # Sort by amount descending
        df = df.sort_values('amount', ascending=False)
        
        # Create a bar chart
        fig = px.bar(df, x='category', y='amount', 
                     title='Monthly Spending by Category',
                     text='amount',
                     color='category')
        
        fig.update_layout(
            xaxis_title='Category',
            yaxis_title='Amount (₹)',
            showlegend=False
        )
        
        fig.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
        
        bar_chart_json = fig.to_json()
        
        # Create a pie chart
        pie_fig = px.pie(df, values='amount', names='category', 
                     title='Monthly Spending Distribution',
                     hole=0.4)
        
        pie_fig.update_traces(textposition='inside', textinfo='percent+label')
        
        pie_chart_json = pie_fig.to_json()
        
        # Calculate metrics
        total_spending = monthly_spending.get("total_expense", 0)
        total_income = monthly_spending.get("total_income", 0)
        savings = monthly_spending.get("savings", 0)
        savings_rate = monthly_spending.get("savings_percentage", 0)
        
        # Identify top spending categories
        top_categories = df.head(3)['category'].tolist()
        
        result = {
            "bar_chart": bar_chart_json,
            "pie_chart": pie_chart_json,
            "metrics": {
                "total_spending": total_spending,
                "total_income": total_income,
                "savings": savings,
                "savings_rate": savings_rate,
                "top_spending_categories": top_categories,
                "month": monthly_spending.get("month", "")
            }
        }
        
        return result
    
    def _analyze_debt(self):
        """Analyze debt situation"""
        loans = self.mcp_service.get_loans()
        credit_cards = self.mcp_service.get_credit_cards()
        
        # Calculate total debt
        total_debt = 0
        for loan_type, loan_data in loans.items():
            total_debt += loan_data.get("outstanding_amount", 0)
        
        for card in credit_cards:
            total_debt += card.get("outstanding_balance", 0)
        
        # Prepare data for the chart
        debt_categories = []
        debt_amounts = []
        
        for loan_type, loan_data in loans.items():
            debt_categories.append(loan_type.replace("_", " ").title())
            debt_amounts.append(loan_data.get("outstanding_amount", 0))
        
        if credit_cards:
            debt_categories.append("Credit Cards")
            debt_amounts.append(sum(card.get("outstanding_balance", 0) for card in credit_cards))
        
        # Create a DataFrame
        df = pd.DataFrame({
            'category': debt_categories,
            'amount': debt_amounts
        })
        
        # Create a pie chart
        fig = px.pie(df, values='amount', names='category', 
                     title='Debt Distribution',
                     hole=0.4)
        
        fig.update_traces(textposition='inside', textinfo='percent+label')
        
        pie_chart_json = fig.to_json()
        
        # Calculate debt metrics
        monthly_income = self.mcp_service.get_spending_summary().get("monthly_summary", {}).get("total_income", 0)
        
        # Calculate total monthly debt payments
        monthly_debt_payment = 0
        for loan_type, loan_data in loans.items():
            monthly_debt_payment += loan_data.get("emi", 0)
        
        # Add minimum credit card payments
        for card in credit_cards:
            monthly_debt_payment += card.get("min_payment_due", 0)
        
        # Calculate debt-to-income ratio
        dti_ratio = (monthly_debt_payment / monthly_income) * 100 if monthly_income > 0 else 0
        
        # Calculate months to debt freedom (assuming no additional debt and paying current EMIs)
        months_to_debt_freedom = 0
        remaining_debt = total_debt
        
        if monthly_debt_payment > 0:
            # Simple calculation without considering interest
            months_to_debt_freedom = remaining_debt / monthly_debt_payment
        
        result = {
            "pie_chart": pie_chart_json,
            "metrics": {
                "total_debt": total_debt,
                "monthly_debt_payment": monthly_debt_payment,
                "debt_to_income_ratio": dti_ratio,
                "months_to_debt_freedom": months_to_debt_freedom
            },
            "loans_detail": [
                {
                    "type": loan_type.replace("_", " ").title(),
                    "outstanding": loan_data.get("outstanding_amount", 0),
                    "interest_rate": loan_data.get("interest_rate", 0),
                    "emi": loan_data.get("emi", 0),
                    "end_date": loan_data.get("end_date", ""),
                    "remaining_tenure": loan_data.get("remaining_tenure", 0)
                } for loan_type, loan_data in loans.items()
            ]
        }
        
        return result
    
    def process_query(self, query):
        """Process a natural language query and provide a response using the Gemini model"""
        
        # Prepare relevant financial data based on the query
        financial_data = self._get_relevant_data_for_query(query)
        
        # Convert financial data to a string format that can be included in the prompt
        financial_data_str = json.dumps(financial_data, indent=2)
        
        # Create a prompt that includes the query and relevant financial data
        prompt = f"""
        Query: {query}
        
        Here is the relevant financial data to help answer this query:
        ```json
        {financial_data_str}
        ```
        
        Based on this financial data, please provide a detailed, personalized response to the query.
        If visualization would be helpful, indicate that with [CHART REQUESTED] and describe the chart requirements.
        If the query requires calculations beyond what's in the data, perform those calculations and explain your methodology.
        """
        
        # Send the query to the model and get a response
        response = self.chat.send_message(prompt)
        
        # Process the response to handle any visualization requests
        processed_response = self._process_response(response.text, query)
        
        return processed_response
    
    def _get_relevant_data_for_query(self, query):
        """Get relevant financial data based on the query"""
        query = query.lower()
        
        # Basic data always included
        data = {
            "user_info": self.mcp_service.get_user_info()
        }
        
        # Check for keywords in the query to determine what additional data to include
        if any(word in query for word in ["money", "cash", "balance", "bank", "account", "savings"]):
            data["bank_accounts"] = self.mcp_service.get_bank_accounts()
        
        if any(word in query for word in ["invest", "mutual", "fund", "stock", "equity", "portfolio", "sip", "underperform", "market"]):
            data["investments"] = {
                "mutual_funds": self.mcp_service.get_mutual_funds(),
                "stocks": self.mcp_service.get_stocks()
            }
            
            # If specifically asking about SIP performance vs market
            if any(word in query for word in ["underperform", "market", "benchmark", "compare"]):
                data["fund_performance_analysis"] = self.mcp_service.analyze_mutual_fund_performance()
        
        if any(word in query for word in ["loan", "debt", "emi", "afford", "home loan", "personal loan"]):
            data["loans"] = self.mcp_service.get_loans()
            
            # If asking about affording a new loan
            if "afford" in query and "loan" in query:
                # Try to extract loan amount from query
                import re
                amount_matches = re.findall(r'(\d+\.?\d*)[lL]', query)
                if amount_matches:
                    loan_amount = float(amount_matches[0]) * 100000  # Convert lakhs to rupees
                    data["loan_affordability"] = self.mcp_service.can_afford_loan(
                        loan_amount=loan_amount, 
                        interest_rate=8.5,  # Assume 8.5% interest rate
                        tenure_years=20     # Assume 20 years tenure
                    )
        
        if any(word in query for word in ["net worth", "networth", "assets", "liabilities", "growing"]):
            data["net_worth"] = self.mcp_service.get_net_worth()
            data["net_worth_history"] = self.mcp_service.get_net_worth_history()
        
        if any(word in query for word in ["spend", "expense", "budget", "category"]):
            data["spending"] = self.mcp_service.get_spending_summary()
        
        if any(word in query for word in ["goal", "target", "retirement", "education", "home"]):
            data["financial_goals"] = self.mcp_service.get_financial_goals()
        
        if any(word in query for word in ["credit", "score", "cibil"]):
            data["credit_score"] = self.mcp_service.get_credit_score()
        
        if any(word in query for word in ["insurance", "policy", "health", "term", "vehicle"]):
            data["insurance"] = self.mcp_service.get_insurance_policies()
        
        if any(word in query for word in ["recommend", "suggestion", "advice"]):
            data["recommendations"] = self.mcp_service.get_recommendations()
        
        # If asking about future projections
        if any(phrase in query for phrase in ["at 40", "by 40", "in 5 years", "in 10 years", "future", "will have", "projection"]):
            age = self.mcp_service.get_user_info().get("age", 30)
            
            # Try to extract target age from query
            import re
            age_matches = re.findall(r'at (\d+)', query)
            
            if age_matches:
                target_age = int(age_matches[0])
                years = target_age - age
                if years > 0:
                    data["projected_net_worth"] = self.mcp_service.get_projected_net_worth(years)
            else:
                # Default to 10-year projection
                data["projected_net_worth"] = self.mcp_service.get_projected_net_worth(10)
        
        return data
    
    def _process_response(self, response_text, original_query):
        """Process the response from the model to include visualizations if requested"""
        
        # Check if visualization is requested
        if "[CHART REQUESTED]" in response_text:
            chart_type = None
            
            # Determine the type of chart needed based on the query and response
            if any(word in original_query.lower() for word in ["net worth", "networth", "grow"]):
                chart_data = self._analyze_net_worth_trend()
                chart_type = "net_worth_trend"
            
            elif any(word in original_query.lower() for word in ["invest", "mutual", "fund", "stock", "portfolio", "sip"]):
                chart_data = self._analyze_investment_performance()
                chart_type = "investment_performance"
            
            elif any(word in original_query.lower() for word in ["spend", "expense", "budget"]):
                chart_data = self._analyze_spending_patterns()
                chart_type = "spending_patterns"
            
            elif any(word in original_query.lower() for word in ["loan", "debt", "emi"]):
                chart_data = self._analyze_debt()
                chart_type = "debt_analysis"
            
            # Remove the chart request tag from the response
            response_text = response_text.replace("[CHART REQUESTED]", "")
            
            # Add a note about the visualization
            if chart_type:
                response_text += f"\n\n[A visualization for {chart_type.replace('_', ' ')} has been generated and is available in the UI.]"
        
        return response_text
    
    def get_visualization_for_query(self, query):
        """Generate visualization based on the query"""
        query = query.lower()
        
        if any(word in query for word in ["net worth", "networth", "grow"]):
            return self._analyze_net_worth_trend(), "net_worth_trend"
        
        elif any(word in query for word in ["invest", "mutual", "fund", "stock", "portfolio", "sip"]):
            return self._analyze_investment_performance(), "investment_performance"
        
        elif any(word in query for word in ["spend", "expense", "budget"]):
            return self._analyze_spending_patterns(), "spending_patterns"
        
        elif any(word in query for word in ["loan", "debt", "emi"]):
            return self._analyze_debt(), "debt_analysis"
        
        return None, None


# Example usage
if __name__ == "__main__":
    from mcp_data_service import MCPDataService
    
    mcp = MCPDataService()
    agent = GeminiFinanceAgent(mcp)
    
    query = "How is my net worth growing?"
    response = agent.process_query(query)
    print(response)
