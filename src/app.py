# %%
import pandas as pd
import numpy as np 

import dash 
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash import dash_table, html, dcc
from dash.exceptions import PreventUpdate
import dash_daq as daq


import base64
import io 

# %%
from A_constants import *
from B_utils import *
from C_prepare_data import *
from D_production_plan import *

# %%
app = dash.Dash(__name__, external_stylesheets = [dbc.themes.BOOTSTRAP])
app.config.suppress_callback_exceptions = True
server = app.server

# %%
# Build the components

upload_data_component = html.Div([
    dcc.Upload(
        id = "upload_data",
        children = html.Div([
            "Drag and drop or ", 
            html.A("Select a file")
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
    ),
    dcc.Store(id = "store_data"),
    html.Div(id = "upload_data_result"),
    html.Div(id = "uploaded_data_display")
])

select_date_range_component = dcc.DatePickerRange(
    start_date = DEFAULT_PLAN_START_DATE,
    end_date = DEFAULT_PLAN_FINISH_DATE,
    id = "select_date_range"
)

select_date_range_button_component = html.Button(
    "Select the date range",
    id = "select_date_range_button"
)

edit_availability_button_component = html.Button(
    "Save the availability",
    id = "save_availability_button"
)

process_button_component = html.Button(
    "Process",
    id = "process_button",
)


# %%
# Design the App layout
app.layout = dbc.Container([
    ## Head
    html.H2("Antenna parts production planning"),
    html.Hr(),
    
    ## 1. Upload the excel file.
    html.H6("1. Upload the Antenna Control Plan excel file."),
    upload_data_component,
    html.Br(),
    
    ## 2. Set the date range for production plan.
    html.H6("2. Select the date range for production plan."), 
    html.P("Select the date range for production plans and click the button. (Default date range is 2 weeks)"),
    select_date_range_component, 
    select_date_range_button_component,
    html.Br(),
    html.Br(),
    html.Div(id = "date_range_result"),
    html.Br(),
    
    html.H6("3. Edit the production availability if needed."),
    html.P("If there is some events (ex. holidays) that have an effect on the daily total production availability, edit the availability for the day from the below table and click the button."),
    html.P("If there is no event, then just check the default availability and click the button."),
    html.Div(id = "availability_table_container"),
    html.Br(),
    dcc.Store(id = "store_availability"),
    edit_availability_button_component,
    html.Br(),
    html.Br(),
    html.Div(id = "availability_result"),
    html.Br(),
    
    html.H6("4. Get the production plan result."), 
    html.P("Click the process button to get the production plan."),
    process_button_component, 
    html.Br(),
    html.Div(id = "result_container"),
    dcc.Store(id = "store_result"),
    html.Br(),
    
    html.H6("5. Check production plan summary."),
    html.Div([
        dbc.Row([
            dbc.Col(html.Div(id = "line2_summary")),
            dbc.Col(html.Div(id = "line3_summary"))
        ])
    ])
])


# %%
# Define interactive flows

# 1. Upload the data
@app.callback(
    [Output("store_data", "data"),
     Output("upload_data_result", "children")],
    [Input("upload_data", "contents"),
     Input("upload_data", "filename")]
)
def save_uploaded_data(contents, filename):
    if contents is None:
        raise PreventUpdate
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    
    try:
        df = pd.read_excel(io.BytesIO(decoded), sheet_name = TARGET_INPUT_SHEET_NAME, skiprows = 3)
        df = df.iloc[1:, 3:]
        upload_data_result = html.Div([
            html.P(f"--> '{TARGET_INPUT_SHEET_NAME}' sheet from '{filename}' file is uploaded. (Uploaded at {datetime.datetime.now().strftime('%H: %M: %S')})"),
            html.P( "--> Check the first 5 rows of the uploaded data. If it is the wrong file, then reupload a file.")
        ])
    
    except:
        df = pd.DataFrame()
        upload_data_result = html.P(f"Uploaded file is wrong. There is no '{TARGET_INPUT_SHEET_NAME}' sheet on the file. Please check the file and try again.")
    
    return [df.to_json(date_format='iso', orient='split'), upload_data_result]

# 1. Show the uploaded data
@app.callback(
    Output("uploaded_data_display", "children"),
    Input("store_data", "data")
)
def display_data_from_store(store_data):
    df = pd.read_json(store_data, orient = 'split')
    
    return html.Div([
        dash_table.DataTable(
            df.head(5).to_dict("records"),
            [{"name": i, "id": i} for i in df.columns]
        )
    ])

# 2. select the date range
@app.callback(
    Output("date_range_result", "children"),
    Input("select_date_range_button", "n_clicks"),
    State("select_date_range", "start_date"), 
    State("select_date_range", "end_date"),
    prevent_initial_call = True
)
def select_date_range(n_clicks, start_date, end_date):
    return html.P(f"--> Date range for the production plans: {start_date} ~ {end_date}")

# 3. show the availability table and save the table
@app.callback(
    Output("availability_table_container", "children"), 
    Input("select_date_range_button", "n_clicks"),
    State("store_data", "data"),
    State("select_date_range", "start_date"),
    State("select_date_range", "end_date"),
    prevent_initial_call = True
)
def show_availability_table(n_clicks, store_data, start_date, end_date):
    if store_data is None:
        # df = pd.DataFrame(columns = ["LINE", "num_wire", "date", "full_available"])
        
        return html.Div[html.P("Please upload the data first."),
                        None]
    else:
        df = pd.read_json(store_data, orient = "split")
    
    df_line_info, df_inventory, df_shipping_plan, df_production_plan, \
    df_daily_full_available, df_uph, df_basic_info = prepare_data(df, start_date, end_date)
    
    df_daily_full_available_pivot = pd.pivot_table(df_daily_full_available.drop("day_of_week", axis = 1), values = "full_available", 
                                              index = ["LINE", "num_wire"], columns = ["date"])
    df_daily_full_available_pivot = df_daily_full_available_pivot.reset_index()
    
    availability_table = dash_table.DataTable(
        df_daily_full_available_pivot.to_dict("records"),
        [{"name": i, "id": i} for i in df_daily_full_available_pivot.columns],
        editable = True,
        id = "availability_table"
    )
    
    return availability_table
    
@app.callback(
    [Output("availability_result", "children"),
     Output("store_availability", "data")],
    Input("save_availability_button", "n_clicks"),
    State("availability_table", "data"),
    prevent_initial_call = True
)
def store_availability(n_clicks, table_data):
    df = pd.DataFrame(table_data)
    
    result = html.Div([
        html.P(f"--> Saved the availability (Clicked at {datetime.datetime.now().strftime('%H: %M: %S')}))"),
    ])
    
    return [result, 
            df.to_json(date_format='iso', orient='split')]

# 4. Process the production planning
@app.callback(
    [Output("result_container", "children"),
     Output("store_result", "data"),
     Output("line2_summary", "children"),
     Output("line3_summary", "children")],
    Input("process_button", "n_clicks"),
    State("store_data", "data"),
    State("select_date_range", "start_date"),
    State("select_date_range", "end_date"),
    State("store_availability", "data"),
    prevent_initial_call = True
)
def process_production_plan(n_clicks, store_data, start_date, end_date, availability_data):
    try:
        df = pd.read_json(store_data, orient = 'split')
        
    except:
        df = pd.DataFrame()
        
    if df.shape[0] == 0:
        result = html.P(f"--> There is no data... Please check the uploaded file. (Clicked at {datetime.datetime.now().strftime('%H: %M: %S')})")
    
    else:
        df_line_info, df_inventory, df_shipping_plan, df_production_plan, \
        df_daily_full_available, df_uph, df_basic_info = prepare_data(df, start_date, end_date)
        
        
        df_daily_full_available_pivot = pd.read_json(availability_data, orient = "split")
        df_daily_full_available_edited = pd.melt(df_daily_full_available_pivot, id_vars = ["LINE", "num_wire"], var_name = "date", value_name = "full_available")
        display(df_daily_full_available_edited.sort_values(["date","LINE", "num_wire"]))
        
        line2_production_summary = Line2_production_plan(df, start_date, end_date, df_daily_full_available_edited)
        line3_production_summary = Line3_production_plan(df, start_date, end_date, df_daily_full_available_edited)
        
        line2_summary_text_list = Line2_production_plan_summary(df, start_date, end_date, line2_production_summary, df_daily_full_available_edited)
        line3_summary_text_list = Line3_production_plan_summary(df, start_date, end_date, line3_production_summary, df_daily_full_available_edited)
        
        line2_production_summary_df = pd.DataFrame(columns = ["PART NUMBER", "LINE", "date", "Production Plan"])
        line3_production_summary_df = pd.DataFrame(columns = ["PART NUMBER", "LINE", "date", "Production Plan"])

        for k, v in line2_production_summary.items():
            for v_k, v_v in v.items():
                line2_production_summary_df = pd.concat([line2_production_summary_df, 
                                                         pd.DataFrame({"PART NUMBER": [v_k], "LINE": ["#2"], "date": [k], "Production Plan": [v_v]})])

        for k, v in line3_production_summary.items():
            for v_k, v_v in v.items():
                line3_production_summary_df = pd.concat([line3_production_summary_df, 
                                                         pd.DataFrame({"PART NUMBER": [v_k], "LINE": ["#3"], "date": [k], "Production Plan": [v_v]})])

        date_list = [start_date]
        for i in range(1, (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days + 1):
            date_list.append((pd.to_datetime(start_date) + datetime.timedelta(days = i)).strftime("%Y-%m-%d"))
        line1_production_summary_df = pd.DataFrame(date_list, columns = ["date"])
        line1_production_summary_df["PART NUMBER"] = "96210-CW100EB"
        line1_production_summary_df["LINE"] = "#1"
        line1_production_summary_df = line1_production_summary_df.merge(df_daily_full_available_edited.loc[df_daily_full_available_edited["LINE"] == "#1", ["date", "full_available"]],
                                                                        how = "left", on = "date").rename(columns = {"full_available": "Production Plan"})
        line1_production_summary_df = line1_production_summary_df[["PART NUMBER", "LINE", "date", "Production Plan"]]

        production_summary_df = pd.concat([line1_production_summary_df, line2_production_summary_df, line3_production_summary_df])

        production_summary_df_pivot = pd.pivot_table(production_summary_df, index = ["PART NUMBER", "LINE"],
                                                     values = "Production Plan", columns = "date").fillna(0).reset_index() \
                                                                                          .sort_values(["LINE", "PART NUMBER"])
        production_summary_df_pivot.index = range(1, production_summary_df_pivot.shape[0] + 1)

        result_4 = html.Div([
            html.P(f"--> Processing the production planning for {start_date} ~ {end_date} (Clicked at {datetime.datetime.now().strftime('%H: %M: %S')})"),
            html.Button("Download the result plan excel file.", id = "download_result_button"),
            dcc.Download(id = "download_result"),
            html.P(" "),
        ])
         
        result_5_line2 = [html.P(text) for text in line2_summary_text_list]
        result_5_line3 = [html.P(text) for text in line3_summary_text_list]
        
    return [result_4, 
            production_summary_df_pivot.to_json(date_format='iso', orient='split'),
            result_5_line2, result_5_line3] 

# 4. Download the result plan.
@app.callback(
    Output("download_result", "data"),
    Input("download_result_button", "n_clicks"),
    State("store_result", "data"),
    prevent_initial_call = True
)
def download_result(n_clicks, store_result):
    df = pd.read_json(store_result, orient = 'split')
    
    return dcc.send_data_frame(df.to_excel, f"antenna_production_plan_{datetime.date.today().strftime('%m-%d-%y')}.xlsx")
# %%
# Run the App
if __name__ == "__main__":
    app.run_server(debug = True)


# %%
