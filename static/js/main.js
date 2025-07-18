// Main JavaScript file for Fi Money MCP Finance Assistant

document.addEventListener('DOMContentLoaded', function() {
    // Navigation between sections
    const sidebarLinks = document.querySelectorAll('#sidebar ul li a');
    const contentSections = document.querySelectorAll('.content-section');
    
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            sidebarLinks.forEach(l => l.parentElement.classList.remove('active'));
            // Add active class to clicked link
            this.parentElement.classList.add('active');
            
            // Hide all content sections
            contentSections.forEach(section => section.classList.remove('active'));
            
            // Show the corresponding section
            const targetId = this.id.replace('-link', '-section');
            if (targetId === 'dashboard-section') {
                document.getElementById('dashboard').classList.add('active');
            } else {
                document.getElementById(targetId).classList.add('active');
            }
        });
    });
    
    // Chat functionality
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const visualizationArea = document.getElementById('visualization-area');
    
    // Handle send button click
    sendButton.addEventListener('click', sendMessage);
    
    // Handle Enter key press in input field
    userInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // Handle suggested query clicks
    const querySuggestions = document.querySelectorAll('.query-suggestion');
    querySuggestions.forEach(suggestion => {
        suggestion.addEventListener('click', function() {
            userInput.value = this.textContent;
            sendMessage();
        });
    });
    
    function sendMessage() {
        const query = userInput.value.trim();
        if (!query) return;
        
        // Add user message to chat
        addMessage(query, 'user');
        
        // Clear input
        userInput.value = '';
        
        // Add loading indicator
        const loadingMessage = addMessage('Thinking...', 'ai', true);
        
        // Send query to backend
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        })
        .then(response => response.json())
        .then(data => {
            // Remove loading message
            loadingMessage.remove();
            
            // Add AI response to chat
            addMessage(data.response, 'ai');
            
            // Handle visualization if available
            if (data.has_visualization) {
                handleVisualization(data.chart_data, data.chart_type);
            }
        })
        .catch(error => {
            // Remove loading message
            loadingMessage.remove();
            
            // Add error message
            addMessage('Sorry, I encountered an error processing your request. Please try again.', 'ai');
            console.error('Error:', error);
        });
    }
    
    function addMessage(content, sender, isLoading = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (isLoading) {
            messageContent.innerHTML = `<p>${content} <span class="loading-dots"><span>.</span><span>.</span><span>.</span></span></p>`;
        } else {
            // Format message with Markdown-like syntax
            const formattedContent = formatMessage(content);
            messageContent.innerHTML = formattedContent;
        }
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom of chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return messageDiv;
    }
    
    function formatMessage(text) {
        // Convert line breaks to HTML
        let formatted = text.replace(/\n/g, '<br>');
        
        // Convert markdown-like syntax
        // Bold
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Italic
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Lists
        const listRegex = /^- (.*)$/gm;
        if (listRegex.test(formatted)) {
            let inList = false;
            const lines = formatted.split('<br>');
            formatted = lines.map(line => {
                if (line.match(/^- (.*)/)) {
                    const content = line.replace(/^- (.*)/, '$1');
                    if (!inList) {
                        inList = true;
                        return `<ul><li>${content}</li>`;
                    } else {
                        return `<li>${content}</li>`;
                    }
                } else {
                    if (inList) {
                        inList = false;
                        return `</ul>${line}`;
                    } else {
                        return line;
                    }
                }
            }).join('<br>');
            
            if (inList) {
                formatted += '</ul>';
            }
        }
        
        return formatted;
    }
    
    function handleVisualization(chartData, chartType) {
        // Clear previous visualizations
        visualizationArea.innerHTML = '';
        
        switch (chartType) {
            case 'net_worth_trend':
                createNetWorthChart(chartData);
                break;
            case 'investment_performance':
                createInvestmentChart(chartData);
                break;
            case 'spending_patterns':
                createSpendingChart(chartData);
                break;
            case 'debt_analysis':
                createDebtChart(chartData);
                break;
            default:
                visualizationArea.innerHTML = '<p>No visualization available for this query.</p>';
        }
    }
    
    function createNetWorthChart(chartData) {
        const chartDiv = document.createElement('div');
        chartDiv.id = 'net-worth-viz';
        chartDiv.style.width = '100%';
        chartDiv.style.height = '100%';
        visualizationArea.appendChild(chartDiv);
        
        const chartJson = JSON.parse(chartData.chart);
        Plotly.newPlot('net-worth-viz', chartJson.data, chartJson.layout);
        
        // Add metrics below the chart
        const metricsDiv = document.createElement('div');
        metricsDiv.className = 'chart-metrics';
        metricsDiv.innerHTML = `
            <p><strong>Current Net Worth:</strong> ₹${formatNumber(chartData.metrics.current_net_worth)}</p>
            <p><strong>Change:</strong> 
                <span class="${chartData.metrics.trend === 'positive' ? 'text-success' : 'text-danger'}">
                    ${chartData.metrics.trend === 'positive' ? '↑' : '↓'} 
                    ₹${formatNumber(Math.abs(chartData.metrics.change_value))} 
                    (${Math.abs(chartData.metrics.change_percent).toFixed(2)}%)
                </span>
            </p>
        `;
        visualizationArea.appendChild(metricsDiv);
    }
    
    function createInvestmentChart(chartData) {
        // Create tabs for different investment charts
        visualizationArea.innerHTML = `
            <ul class="nav nav-tabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="portfolio-tab" data-bs-toggle="tab" data-bs-target="#portfolio-chart" type="button">Portfolio</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="mutual-funds-tab" data-bs-toggle="tab" data-bs-target="#mutual-funds-chart" type="button">Mutual Funds</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="stocks-tab" data-bs-toggle="tab" data-bs-target="#stocks-chart" type="button">Stocks</button>
                </li>
            </ul>
            <div class="tab-content">
                <div class="tab-pane fade show active" id="portfolio-chart" role="tabpanel"></div>
                <div class="tab-pane fade" id="mutual-funds-chart" role="tabpanel"></div>
                <div class="tab-pane fade" id="stocks-chart" role="tabpanel"></div>
            </div>
        `;
        
        // Create portfolio allocation chart
        if (chartData.portfolio_allocation_chart) {
            const portfolioChartJson = JSON.parse(chartData.portfolio_allocation_chart);
            Plotly.newPlot('portfolio-chart', portfolioChartJson.data, portfolioChartJson.layout);
        }
        
        // Create mutual funds chart
        if (chartData.mutual_funds_chart) {
            const mfChartJson = JSON.parse(chartData.mutual_funds_chart);
            Plotly.newPlot('mutual-funds-chart', mfChartJson.data, mfChartJson.layout);
        }
        
        // Create stocks chart
        if (chartData.stocks_chart) {
            const stocksChartJson = JSON.parse(chartData.stocks_chart);
            Plotly.newPlot('stocks-chart', stocksChartJson.data, stocksChartJson.layout);
        }
        
        // Add metrics
        const metricsDiv = document.createElement('div');
        metricsDiv.className = 'chart-metrics';
        metricsDiv.innerHTML = `
            <p><strong>Total Investment Value:</strong> ₹${formatNumber(chartData.metrics.total_investment_value)}</p>
            <p><strong>Average Return:</strong> ${chartData.metrics.weighted_average_return.toFixed(2)}%</p>
        `;
        
        if (chartData.metrics.best_performing_asset) {
            metricsDiv.innerHTML += `
                <p><strong>Best Performing:</strong> ${chartData.metrics.best_performing_asset.name} 
                (${chartData.metrics.best_performing_asset.return.toFixed(2)}%)</p>
            `;
        }
        
        if (chartData.metrics.worst_performing_asset) {
            metricsDiv.innerHTML += `
                <p><strong>Worst Performing:</strong> ${chartData.metrics.worst_performing_asset.name} 
                (${chartData.metrics.worst_performing_asset.return.toFixed(2)}%)</p>
            `;
        }
        
        visualizationArea.appendChild(metricsDiv);
    }
    
    function createSpendingChart(chartData) {
        // Create tabs for different spending charts
        visualizationArea.innerHTML = `
            <ul class="nav nav-tabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="pie-tab" data-bs-toggle="tab" data-bs-target="#spending-pie-chart" type="button">Distribution</button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="bar-tab" data-bs-toggle="tab" data-bs-target="#spending-bar-chart" type="button">By Category</button>
                </li>
            </ul>
            <div class="tab-content">
                <div class="tab-pane fade show active" id="spending-pie-chart" role="tabpanel"></div>
                <div class="tab-pane fade" id="spending-bar-chart" role="tabpanel"></div>
            </div>
        `;
        
        // Create pie chart
        if (chartData.pie_chart) {
            const pieChartJson = JSON.parse(chartData.pie_chart);
            Plotly.newPlot('spending-pie-chart', pieChartJson.data, pieChartJson.layout);
        }
        
        // Create bar chart
        if (chartData.bar_chart) {
            const barChartJson = JSON.parse(chartData.bar_chart);
            Plotly.newPlot('spending-bar-chart', barChartJson.data, barChartJson.layout);
        }
        
        // Add metrics
        const metricsDiv = document.createElement('div');
        metricsDiv.className = 'chart-metrics';
        metricsDiv.innerHTML = `
            <p><strong>Month:</strong> ${chartData.metrics.month}</p>
            <p><strong>Total Income:</strong> ₹${formatNumber(chartData.metrics.total_income)}</p>
            <p><strong>Total Expenses:</strong> ₹${formatNumber(chartData.metrics.total_spending)}</p>
            <p><strong>Savings:</strong> ₹${formatNumber(chartData.metrics.savings)} (${chartData.metrics.savings_rate.toFixed(2)}%)</p>
            <p><strong>Top Categories:</strong> ${chartData.metrics.top_spending_categories.join(', ')}</p>
        `;
        visualizationArea.appendChild(metricsDiv);
    }
    
    function createDebtChart(chartData) {
        // Create chart div
        const chartDiv = document.createElement('div');
        chartDiv.id = 'debt-viz';
        chartDiv.style.width = '100%';
        chartDiv.style.height = '100%';
        visualizationArea.appendChild(chartDiv);
        
        // Create pie chart
        if (chartData.pie_chart) {
            const pieChartJson = JSON.parse(chartData.pie_chart);
            Plotly.newPlot('debt-viz', pieChartJson.data, pieChartJson.layout);
        }
        
        // Add metrics
        const metricsDiv = document.createElement('div');
        metricsDiv.className = 'chart-metrics';
        metricsDiv.innerHTML = `
            <p><strong>Total Debt:</strong> ₹${formatNumber(chartData.metrics.total_debt)}</p>
            <p><strong>Monthly Payment:</strong> ₹${formatNumber(chartData.metrics.monthly_debt_payment)}</p>
            <p><strong>Debt-to-Income Ratio:</strong> ${chartData.metrics.debt_to_income_ratio.toFixed(2)}%</p>
            <p><strong>Est. Months to Debt Freedom:</strong> ${Math.ceil(chartData.metrics.months_to_debt_freedom)}</p>
        `;
        visualizationArea.appendChild(metricsDiv);
    }
    
    // Helper function to format numbers with commas
    function formatNumber(number) {
        return new Intl.NumberFormat('en-IN').format(parseFloat(number).toFixed(2));
    }
    
    // Handle export data
    document.getElementById('export-data-link').addEventListener('click', function(e) {
        e.preventDefault();
        
        fetch('/data/all')
        .then(response => response.json())
        .then(data => {
            // Create a download link for the JSON data
            const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
            const downloadAnchorNode = document.createElement('a');
            downloadAnchorNode.setAttribute("href", dataStr);
            downloadAnchorNode.setAttribute("download", "fi_money_mcp_data.json");
            document.body.appendChild(downloadAnchorNode); // Required for Firefox
            downloadAnchorNode.click();
            downloadAnchorNode.remove();
        })
        .catch(error => {
            console.error('Error exporting data:', error);
            alert('Error exporting data. Please try again.');
        });
    });
});
