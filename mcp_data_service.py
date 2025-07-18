import json
import os
from datetime import datetime

class MCPDataService:
    """Service to interact with Fi Money's MCP data"""
    
    def __init__(self, data_file_path='mcp_data.json'):
        """Initialize the MCP Data Service with the path to the data file"""
        self.data_file_path = data_file_path
        self.data = self._load_data()
    
    def _load_data(self):
        """Load data from the JSON file"""
        try:
            with open(self.data_file_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            print(f"Error loading MCP data: {str(e)}")
            return {}
    
    def get_user_info(self):
        """Get basic user information"""
        return self.data.get('user', {})
    
    def get_bank_accounts(self):
        """Get all bank accounts"""
        return self.data.get('accounts', {}).get('bank_accounts', [])
    
    def get_total_bank_balance(self):
        """Get total balance across all bank accounts"""
        accounts = self.get_bank_accounts()
        return sum(account.get('balance', 0) for account in accounts)
    
    def get_credit_cards(self):
        """Get all credit cards"""
        return self.data.get('accounts', {}).get('credit_cards', [])
    
    def get_total_credit_card_debt(self):
        """Get total outstanding balance across all credit cards"""
        credit_cards = self.get_credit_cards()
        return sum(card.get('outstanding_balance', 0) for card in credit_cards)
    
    def get_investments(self):
        """Get all investments"""
        return self.data.get('investments', {})
    
    def get_mutual_funds(self):
        """Get all mutual funds"""
        return self.data.get('investments', {}).get('mutual_funds', [])
    
    def get_stocks(self):
        """Get all stocks"""
        return self.data.get('investments', {}).get('stocks', [])
    
    def get_total_mutual_fund_value(self):
        """Get total current value of all mutual funds"""
        mutual_funds = self.get_mutual_funds()
        return sum(fund.get('current_value', 0) for fund in mutual_funds)
    
    def get_total_stock_value(self):
        """Get total current value of all stocks"""
        stocks = self.get_stocks()
        return sum(stock.get('current_value', 0) for stock in stocks)
    
    def get_retirement_accounts(self):
        """Get all retirement accounts (EPF and PPF)"""
        investments = self.data.get('investments', {})
        return {
            'epf': investments.get('epf', {}),
            'ppf': investments.get('ppf', {})
        }
    
    def get_loans(self):
        """Get all loans"""
        return self.data.get('loans', {})
    
    def get_total_loan_outstanding(self):
        """Get total outstanding loan amount"""
        loans = self.get_loans()
        total = 0
        for loan_type, loan_data in loans.items():
            total += loan_data.get('outstanding_amount', 0)
        return total
    
    def get_credit_score(self):
        """Get credit score information"""
        return self.data.get('credit_score', {})
    
    def get_insurance_policies(self):
        """Get all insurance policies"""
        return self.data.get('insurance', {})
    
    def get_spending_summary(self):
        """Get spending summary information"""
        return self.data.get('spending', {})
    
    def get_monthly_spending(self):
        """Get monthly spending breakdown"""
        return self.data.get('spending', {}).get('monthly_summary', {})
    
    def get_yearly_spending(self):
        """Get yearly spending breakdown"""
        return self.data.get('spending', {}).get('yearly_summary', {})
    
    def get_recent_transactions(self):
        """Get recent transactions"""
        return self.data.get('spending', {}).get('recent_transactions', [])
    
    def get_financial_goals(self):
        """Get financial goals"""
        return self.data.get('financial_goals', [])
    
    def get_net_worth(self):
        """Get net worth information"""
        return self.data.get('net_worth', {})
    
    def get_net_worth_history(self):
        """Get net worth history"""
        return self.data.get('net_worth', {}).get('history', [])
    
    def get_recommendations(self):
        """Get financial recommendations"""
        return self.data.get('recommendations', [])
    
    def get_projected_net_worth(self, years):
        """
        Estimate projected net worth after specified number of years
        based on current saving and spending patterns
        """
        current_net_worth = self.data.get('net_worth', {}).get('net_worth', 0)
        monthly_savings = self.data.get('spending', {}).get('monthly_summary', {}).get('savings', 0)
        yearly_savings = monthly_savings * 12
        
        # Simple projection assuming a 8% annual return on investments
        annual_return_rate = 0.08
        projected_net_worth = current_net_worth
        
        for _ in range(years):
            # Add yearly savings
            projected_net_worth += yearly_savings
            
            # Apply investment returns (assuming positive net worth)
            if projected_net_worth > 0:
                projected_net_worth += projected_net_worth * annual_return_rate
        
        return projected_net_worth
    
    def can_afford_loan(self, loan_amount, interest_rate, tenure_years):
        """
        Determine if user can afford a new loan based on income and existing obligations
        Returns a tuple of (can_afford, max_affordable_emi, recommended_emi)
        """
        # Get monthly income
        monthly_income = self.data.get('spending', {}).get('monthly_summary', {}).get('total_income', 0)
        
        # Calculate EMI for the requested loan
        r = interest_rate / (12 * 100)  # Monthly interest rate
        n = tenure_years * 12  # Total number of months
        emi = (loan_amount * r * ((1 + r) ** n)) / (((1 + r) ** n) - 1)
        
        # Get existing EMIs
        existing_emi = 0
        loans = self.get_loans()
        for loan_type, loan_data in loans.items():
            existing_emi += loan_data.get('emi', 0)
        
        # Calculate total debt burden
        total_emi = existing_emi + emi
        
        # Calculate debt-to-income ratio (should ideally be below 50%)
        dti_ratio = total_emi / monthly_income if monthly_income > 0 else 1
        
        # Recommended maximum EMI (40% of income)
        recommended_max_emi = monthly_income * 0.4
        
        # Maximum affordable EMI (50% of income minus existing EMIs)
        max_affordable_emi = (monthly_income * 0.5) - existing_emi
        
        # Determine if affordable (DTI ratio < 50% and new total EMI < 50% of income)
        can_afford = dti_ratio < 0.5 and max_affordable_emi > 0
        
        return {
            "can_afford": can_afford,
            "requested_emi": round(emi, 2),
            "max_affordable_emi": round(max_affordable_emi, 2),
            "recommended_emi": round(min(recommended_max_emi - existing_emi, max_affordable_emi), 2),
            "debt_to_income_ratio": round(dti_ratio * 100, 2),
            "existing_emi": round(existing_emi, 2),
            "monthly_income": round(monthly_income, 2)
        }
    
    def analyze_mutual_fund_performance(self):
        """
        Analyze mutual fund performance compared to market benchmarks
        Returns a list of underperforming and overperforming funds
        """
        mutual_funds = self.get_mutual_funds()
        
        # Define benchmark returns for different categories
        benchmarks = {
            "Equity - Large Cap": 12.0,  # Nifty 50 average annual return
            "Equity - Mid Cap": 14.0,    # Nifty Midcap 100 average annual return
            "Debt - Corporate Bond": 7.0  # Corporate Bond index average annual return
        }
        
        underperforming = []
        outperforming = []
        
        for fund in mutual_funds:
            category = fund.get("category", "")
            benchmark_return = benchmarks.get(category, 10.0)  # Default to 10% if category not found
            
            # Compare 1-year returns to benchmark
            fund_1y_return = fund.get("returns", {}).get("1y", 0)
            
            # Calculate performance difference
            diff = fund_1y_return - benchmark_return
            
            fund_analysis = {
                "name": fund.get("name", ""),
                "category": category,
                "fund_return_1y": fund_1y_return,
                "benchmark_return": benchmark_return,
                "difference": round(diff, 2)
            }
            
            if diff < -1.0:  # Underperforming by more than 1%
                underperforming.append(fund_analysis)
            elif diff > 1.0:  # Outperforming by more than 1%
                outperforming.append(fund_analysis)
        
        return {
            "underperforming": underperforming,
            "outperforming": outperforming
        }


# Example usage
if __name__ == "__main__":
    mcp = MCPDataService()
    user_info = mcp.get_user_info()
    print(f"User: {user_info['name']}")
    print(f"Total Bank Balance: ₹{mcp.get_total_bank_balance():,.2f}")
    print(f"Net Worth: ₹{mcp.get_net_worth()['net_worth']:,.2f}")
