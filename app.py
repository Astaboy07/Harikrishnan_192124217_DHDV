import requests
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import numpy as np

API_KEY = "0580ZZYG5OQTVS3V"  # Replace with your API key
API_URL = "https://www.alphavantage.co/query"
SYMBOL = "NVDA"
START_DATE = "2024-01-01"       # Starting data from January 1
HIGHLIGHT_DATE = "2025-01-24"   # Highlight data from January 24, 2025 onward

def fetch_stock_data(symbol):
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": API_KEY
    }
    response = requests.get(API_URL, params=params)
    data = response.json()
    return data.get("Time Series (Daily)", {})

def filter_stock_data(stock_data):
    # Filter for dates greater than or equal to START_DATE
    filtered_data = {
        date: float(values["4. close"])
        for date, values in stock_data.items()
        if date >= START_DATE
    }
    sorted_dates = sorted(filtered_data.keys())
    return sorted_dates, [filtered_data[date] for date in sorted_dates]

stock_data = fetch_stock_data(SYMBOL)
dates, prices = filter_stock_data(stock_data)

def predict_next_day_price(prices):
    # A simple prediction using the average daily difference
    return round(prices[-1] + (np.mean(np.diff(prices))), 2)

app = dash.Dash(__name__)
server = app.server  # Expose the server for deployment if needed

app.layout = html.Div([
    html.H1(
        "Stock Price of Nvidia from Jan 1 with Highlight from Jan 24, 2025", 
        style={'textAlign': 'center', 'backgroundColor': 'black', 'color': 'white', 'padding': '10px'}
    ),
    dcc.RadioItems(
        id="graph-type",
        options=[
            {"label": "Line Chart", "value": "line"},
            {"label": "Bar Chart", "value": "bar"},
            {"label": "Candlestick Chart", "value": "candlestick"}
        ],
        value="line",
        inline=True,
        style={'color': 'white'}
    ),
    dcc.Graph(id="stock-chart"),
    html.H3("Stock Statistics", style={'margin-top': '20px', 'color': 'white'}),
    html.P(id="stock-mean", style={'color': 'white'}),
    html.P(id="stock-median", style={'color': 'white'}),
    html.P(id="stock-prediction", style={'color': 'white'}),
    html.Div(id="stock-table"),
    html.Br(),
    dcc.Dropdown(
        id="date-dropdown",
        options=[{'label': d, 'value': d} for d in dates],
        placeholder="Select a date",
        style={'width': '50%', 'margin': 'auto'}
    ),
    html.Div(id="selected-metrics")
], style={'backgroundColor': 'black', 'padding': '20px'})

@app.callback(
    [Output("stock-chart", "figure"),
     Output("stock-mean", "children"),
     Output("stock-median", "children"),
     Output("stock-prediction", "children"),
     Output("stock-table", "children")],
    [Input("graph-type", "value")]
)
def update_graph(graph_type):
    mean_price = round(np.mean(prices), 2)
    median_price = round(np.median(prices), 2)
    predicted_price = predict_next_day_price(prices)
    
    # Split data into before and after the highlight date
    dates_before = [d for d in dates if d < HIGHLIGHT_DATE]
    prices_before = [prices[i] for i, d in enumerate(dates) if d < HIGHLIGHT_DATE]
    dates_after = [d for d in dates if d >= HIGHLIGHT_DATE]
    prices_after = [prices[i] for i, d in enumerate(dates) if d >= HIGHLIGHT_DATE]
    
    if graph_type == "line":
        trace1 = go.Scatter(
            x=dates_before, y=prices_before, mode="lines+markers", 
            name="NVDA (Before)", line=dict(color='blue')
        )
        trace2 = go.Scatter(
            x=dates_after, y=prices_after, mode="lines+markers", 
            name="NVDA (After)", line=dict(color='red')
        )
        figure = go.Figure(data=[trace1, trace2])
    elif graph_type == "bar":
        trace1 = go.Bar(
            x=dates_before, y=prices_before, 
            name="NVDA (Before)", marker_color='blue'
        )
        trace2 = go.Bar(
            x=dates_after, y=prices_after, 
            name="NVDA (After)", marker_color='red'
        )
        figure = go.Figure(data=[trace1, trace2])
    elif graph_type == "candlestick":
        figure = go.Figure(
            data=[go.Candlestick(
                x=dates,
                open=[float(stock_data[date]["1. open"]) for date in dates],
                high=[float(stock_data[date]["2. high"]) for date in dates],
                low=[float(stock_data[date]["3. low"]) for date in dates],
                close=prices,
                name="NVDA Candlestick"
            )]
        )
        # Add a vertical rectangle to highlight the period from HIGHLIGHT_DATE to the last date
        figure.add_vrect(
            x0=HIGHLIGHT_DATE, x1=dates[-1],
            fillcolor="rgba(255,0,0,0.2)",
            line_width=0,
            annotation_text="Highlighted",
            annotation_position="top left"
        )
    
    figure.update_layout(
        title={"text": "Stock Price of Nvidia from Jan 1 with Highlight from Jan 24, 2025", "font": {"color": "white"}},
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        paper_bgcolor="black",
        plot_bgcolor="black",
        font_color="white",
        shapes=[
            # For non-candlestick charts, add a vertical dashed line at the highlight date
            {
                "type": "line",
                "x0": HIGHLIGHT_DATE,
                "x1": HIGHLIGHT_DATE,
                "y0": min(prices),
                "y1": max(prices),
                "line": {"color": "red", "width": 2, "dash": "dash"},
            }
        ]
    )
    
    # Prepare table data: End Price and Predicted Price
    end_price = prices[-1] if prices else "N/A"
    
    table = html.Table(
        children=[
            html.Thead(
                html.Tr([
                    html.Th("Metric", style={'padding': '8px', 'border': '1px solid white'}),
                    html.Th("Value", style={'padding': '8px', 'border': '1px solid white'})
                ]),
                style={'backgroundColor': '#333', 'color': 'white'}
            ),
            html.Tbody([
                html.Tr([
                    html.Td("End Price", style={'padding': '8px', 'border': '1px solid white'}),
                    html.Td(f"${end_price}", style={'padding': '8px', 'border': '1px solid white'})
                ]),
                html.Tr([
                    html.Td("Predicted Next Price", style={'padding': '8px', 'border': '1px solid white'}),
                    html.Td(f"${predicted_price}", style={'padding': '8px', 'border': '1px solid white'})
                ])
            ])
        ],
        style={'width': '50%', 'margin': 'auto', 'marginTop': '20px', 'borderCollapse': 'collapse'}
    )
    
    return (
        figure, 
        f"Mean Price: ${mean_price}", 
        f"Median Price: ${median_price}", 
        f"Predicted Next Closing Price: ${predicted_price}",
        table
    )

@app.callback(
    Output("selected-metrics", "children"),
    [Input("date-dropdown", "value")]
)
def update_selected_metrics(selected_date):
    if selected_date is None:
        return ""
    data = stock_data.get(selected_date)
    if not data:
        return f"No data available for {selected_date}"
    open_price = data.get("1. open", "N/A")
    high_price = data.get("2. high", "N/A")
    low_price = data.get("3. low", "N/A")
    close_price = data.get("4. close", "N/A")
    return html.Div([
         html.P(f"Selected Date: {selected_date}"),
         html.P(f"Open: ${open_price}"),
         html.P(f"High: ${high_price}"),
         html.P(f"Low: ${low_price}"),
         html.P(f"Close: ${close_price}")
    ], style={'color': 'red', 'textAlign': 'center'})

if __name__ == "__main__":
    app.run_server(debug=True)
