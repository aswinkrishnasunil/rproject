import pandas as pd
import plotly.express as px
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go



# Read the CSV files for IMO and ports data
ship_data = pd.read_csv("https://dl.dropboxusercontent.com/scl/fi/4bz3qrjqhbevtlqn4w131/imo_tracking.csv?rlkey=w9evtnyx2oo1wwx2sdaw0190r&dl=0")
#ship_data = pd.read_csv("imo_tracking.csv")
ports_data = pd.read_csv("https://dl.dropboxusercontent.com/scl/fi/4h83p47fpaz5v1tnhaw69/ports.csv?rlkey=1erpymfq8eq6fzst5dcxi0wt3&dl=0")
#ports_data = pd.read_csv("ports.csv")
regions = pd.read_csv("https://dl.dropboxusercontent.com/scl/fi/dhow2fvxtibo46gjget76/regions.csv?rlkey=xsoa08k36f2z8q4rqpy4p29y8&dl=0")
#regions = pd.read_csv("regions.csv")
yy_ship_count = pd.read_csv("https://dl.dropboxusercontent.com/scl/fi/gzu9k87fxiutcf0q6uqo3/yy_ship_count.csv?rlkey=04hv0trgaoe0myk3pjcsmnu7e&dl=0")
#yy_ship_count = pd.read_csv("yy_ship_count.csv")
combined_data = pd.merge(ship_data, yy_ship_count, on='imo', how='left')

#combined_data['seen_date'] = pd.to_datetime(combined_data['seen_date'], format='%Y-%m-%d %H:%M:%S')
#combined_data['seen_date_hour'] = combined_data['seen_date'].dt.hour  # Extract hours from seen_date

#df['seen_date_hour'] = df['seen_date'].dt.hour  # Extract hours from seen_date
combined_data['seen_date'] = pd.to_datetime(combined_data['seen_date'], format='%Y-%m-%d %H:%M:%S')
#df['cumulative_hours'] = (df['seen_date'] - df['seen_date'].min()).dt.total_seconds() / 3600 + 1
combined_data['cumulative_hours'] = (combined_data['seen_date'] - combined_data['seen_date'].iloc[0]).dt.total_seconds() / 3600

#latest_locations = ship_data.groupby('imo').apply(lambda x: x.loc[x['seen_date'].idxmax()]).reset_index(drop=True)

#a=combined_data[['seen_date','cumulative_hours','imo','lat','lon']]
#print(a.head(52))

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Get unique values for the source region dropdown
source_regions = ship_data['source_region'].unique()

app.layout = dbc.Container([
    
    dbc.Row([
        dbc.Col(
            html.Div([
                dcc.Input(
                    id='imo-search',
                    type='text',
                    placeholder='Enter IMO number...',
                    value='',  # Initial value of the search box
                    style={'width': '100%'}  # Adjust width to 100%
                ),
                html.Label("Regions"),
                dcc.Dropdown(
                    id='source-region-dropdown',
                    options=[{'label': 'Select All', 'value': 'selectall'},
                             {'label': 'Deselect All', 'value': 'deselectall'}] + [{'label': region, 'value': region} for region in source_regions],
                    value=['selectall'],  # Set default value as 'selectall'
                    multi=True,  # Enable multiple selection
                    style={'width': '100%'}  # Adjust width to 100%
                ),
                html.Label("Select Sub-regions"),
                dcc.Dropdown(
                    id='source-subregion-dropdown',
                    options=[
                        {'label': 'Select All', 'value': 'selectall'},
                        {'label': 'Deselect All', 'value': 'deselectall'}
                    ] + [{'label': subregion, 'value': subregion} for subregion in ship_data['source_subregion'].unique()],
                    value=[],  # Initial value for subregion dropdown
                    multi=True,  # Enable multiple selection
                    style={'width': '100%'}  # Adjust width to 100%
                ),
                html.Label("Select Ports"),
                dcc.Dropdown(
                    id='source-port-dropdown',
                    options=[
                        {'label': 'Select All', 'value': 'selectall'},
                        {'label': 'Deselect All', 'value': 'deselectall'}
                    ] + [{'label': port, 'value': port} for port in ship_data['source_port'].unique()],
                    value=[],  # Initial value for port dropdown
                    multi=True,  # Enable multiple selection
                    style={'width': '100%'}  # Adjust width to 100%
                ),
                html.Label("Dest Region"),
                dcc.Dropdown(
                    id='dest-region-dropdown',
                    options=[
                        {'label': 'Select All', 'value': 'selectall'},
                        {'label': 'Deselect All', 'value': 'deselectall'}
                    ] +[{'label': region, 'value': region} for region in regions['region'].unique()],
                    value=[],  # Initial value for region dropdown
                    multi=True,  # Enable multiple selection
                    style={'width': '100%'}  # Adjust width to 100%
                ),

                html.Label("Dest Sub-region"),
                dcc.Dropdown(
                    id='dest-subregion-dropdown',
                    options=[
                        {'label': 'Select All', 'value': 'selectall'},
                        {'label': 'Deselect All', 'value': 'deselectall'}
                    ] + [{'label': subregion, 'value': subregion} for subregion in combined_data['subregion'].dropna().unique()],
                    value=[],  # Initial value for subregion dropdown
                    multi=True,  # Enable multiple selection
                    style={'width': '100%'}  # Adjust width to 100%
                ),

                html.Label("Dest port"),
                dcc.Dropdown(
                    id='dest-port-dropdown',
                    options=[
                        {'label': 'Select All', 'value': 'selectall'},
                        {'label': 'Deselect All', 'value': 'deselectall'}
                    ] + [{'label': port_name, 'value': port_name} for port_name in combined_data['port_name'].dropna().unique()],
                    value=[],  # Initial value for subregion dropdown
                    multi=True,  # Enable multiple selection
                    style={'width': '100%'}  # Adjust width to 100%
                ),
                dbc.Label("Idle Ships"),
                dbc.Checklist(
                    options=[
                        {"label": "idle", "value": 1},
                        {"label": "active", "value": 0},
                    ],
                    
                    value=[],
                    id="checklist-idle-input",
                    inline=True,
                ),
                dbc.Label("empty full"),
                dbc.Checklist(
                    options=[
                        {"label": "empty", "value": 1},
                        {"label": "full", "value": 0},
                    ],
                    
                    value=[],
                    id="checklist-emptyfull-input",
                    inline=True,
                ),
                dbc.Label("Max Full Draft (meter)"),
                dcc.Slider(
                    id='fulldraft-slider',
                    min=11,
                    max=14,
                    step=0.2,
                    marks={value: str(value) for value in range(11, 15) if value % 1 == 0},

                    value=12,  # Initial value
                ),  
                
                 # Display the counts of 'Full' and 'Empty' values
                html.Div(id='ef-counts'),
                
                html.Label('Select a Time Range (in hours):'),
                dcc.Slider(
                    id='time-range-slider',
                    min=1,
                    max=81,
                    step=1,
                    marks={i: str(i) for i in range(1, 81, 8)},
                    value=30  # Initial time range value
                ),
                html.Label('idle if no movement in (days)'),
                dcc.Slider(
                    id='idle-slider',
                    min=1,
                    max=8,
                    step=1,
                    marks={i: str(i) for i in range(1, 9, 1)},
                    value=5  # Initial time range value

                )

                 # Display the counts of 'Full' and 'Empty' values
                #html.Div(id='ef-counts')

                          
   
                
                # Output for displaying the filtered data
           
            ]),
            width=3  # Left side column width
        ),
        dbc.Col(
            html.Div([
                dcc.Graph(
                    id='map'
                )
            ]),
            width=8  # Right side column width
        )
    ], justify="left")  # Center-aligns the row
])  
print("part 1")  
@app.callback(
    Output('source-subregion-dropdown', 'options'),
    [Input('source-region-dropdown', 'value')]
)
def update_subregion_options(selected_regions):
    if 'selectall' in selected_regions:
        filtered_ship_data = ship_data
        selected_regions.remove('selectall')
    elif 'deselectall' in selected_regions:
        filtered_ship_data = pd.DataFrame()  # Empty DataFrame when 'deselectall' is selected
        selected_regions.remove('deselectall')
    else:
        filtered_ship_data = ship_data[ship_data['source_region'].isin(selected_regions)]

    subregions = filtered_ship_data['source_subregion'].unique()
    return [{'label': subregion, 'value': subregion} for subregion in subregions]

@app.callback(
    Output('source-port-dropdown', 'options'),
    [Input('source-subregion-dropdown', 'value')]
)
def update_port_options(selected_subregions):
    filtered_ship_data = ship_data[ship_data['source_subregion'].isin(selected_subregions)]
    ports = filtered_ship_data['source_port'].unique()
    return [{'label': port, 'value': port} for port in ports]



@app.callback(
    Output('dest-subregion-dropdown', 'options'),
    [Input('dest-region-dropdown', 'value')]
)
def update_dest_subregion_options(selected_dest_regions):
    if 'selectall' in selected_dest_regions:
        subregions = combined_data['subregion'].dropna().unique()
        return [{'label': subregion, 'value': subregion} for subregion in subregions]

    elif 'deselectall' in selected_dest_regions:
        return []

    else:
        filtered_combined_data = combined_data[combined_data['region'].isin(selected_dest_regions)]
        subregions = filtered_combined_data['subregion'].dropna().unique()
        return [{'label': subregion, 'value': subregion} for subregion in subregions]


@app.callback(
    Output('dest-port-dropdown', 'options'),
    [Input('dest-subregion-dropdown', 'value')]
)
def update_dest_port_options(selected_dest_subregions):
    if 'selectall' in selected_dest_subregions:
        filtered_combined_data = combined_data
        selected_dest_subregions.remove('selectall')
    elif 'deselectall' in selected_dest_subregions:
        filtered_combined_data = pd.DataFrame()  # Empty DataFrame when 'deselectall' is selected
        selected_dest_subregions.remove('deselectall')
    else:
        filtered_combined_data = combined_data[combined_data['subregion'].isin(selected_dest_subregions)]

    ports = filtered_combined_data['port_name'].dropna().unique()
    return [{'label': port, 'value': port} for port in ports]



print("part 2")

@app.callback(
    Output('map', 'figure'),
    Output('ef-counts', 'children'),
    [Input('imo-search', 'value'),
     Input('source-region-dropdown', 'value'),
     Input('source-subregion-dropdown', 'value'),
     Input('source-port-dropdown', 'value'),
     Input('dest-region-dropdown', 'value'),
     Input('dest-subregion-dropdown', 'value'),
     Input('dest-port-dropdown', 'value'),
     Input('checklist-idle-input', 'value'),
     Input('checklist-emptyfull-input', 'value'),
     Input('fulldraft-slider','value'),
     Input('time-range-slider', 'value'),
     Input('idle-slider','value'),
     
     ]
)

def update_map(imo_number, selected_regions,selected_subregions,selected_ports,dest_regions,dest_subregions,dest_ports,
               selected_idle_status,selected_emptyfull_status,fulldraft,selected_time_range,idle_slider):
    filtered_ship_data = combined_data  # Initialize with the combined data

    #print(combined_data.columns.tolist())
    #print(filtered_ship_data['idle_y'].head())

     # Filter based on selected idle status
    #if selected_idle_status:
    #    filtered_ship_data = combined_data[combined_data['idle'].isin(selected_idle_status)]

    

    print("part 3")
        
    if idle_slider:
        filtered_ship_data = filtered_ship_data[filtered_ship_data['idle_x'] <= idle_slider]

    
    

    if fulldraft:
        filtered_ship_data = filtered_ship_data[filtered_ship_data['max_draft'] <= fulldraft]

    if selected_emptyfull_status:
        filtered_ship_data = filtered_ship_data[filtered_ship_data['empty_full'].isin(selected_emptyfull_status)]

    if selected_idle_status:
        filtered_ship_data = filtered_ship_data[filtered_ship_data['idle_y'].isin(selected_idle_status)]


    if dest_ports and 'selectall' not in dest_ports:
        filtered_ship_data = filtered_ship_data[filtered_ship_data['port_name'].isin(dest_ports)]


    if dest_regions and 'selectall' not in dest_regions:
        filtered_ship_data = filtered_ship_data[filtered_ship_data['region'].isin(dest_regions)]

    if dest_subregions:
        filtered_ship_data = filtered_ship_data[filtered_ship_data['subregion'].isin(dest_subregions)]

    # Filter data based on selected regions
    if selected_regions and 'selectall' not in selected_regions:
        filtered_ship_data = filtered_ship_data[filtered_ship_data['source_region'].isin(selected_regions)]

    # Filter data based on sub regions
    if selected_subregions:
        filtered_ship_data = filtered_ship_data[filtered_ship_data['source_subregion'].isin(selected_subregions)]

    # Filter data based on IMO number if provided
    if imo_number and imo_number.isdigit():
        imo_number = int(imo_number)
        filtered_ship_data = filtered_ship_data[filtered_ship_data['imo'] == imo_number]

    if selected_ports:
        filtered_ship_data = filtered_ship_data[filtered_ship_data['source_port'].isin(selected_ports)]
    
    
    print ("part 4")

    # Convert 'seen_date' column to datetime
    filtered_ship_data['seen_date'] = pd.to_datetime(filtered_ship_data['seen_date'])

    # Group by 'imo' and get the latest 'seen_date' for each IMO
    latest_dates = filtered_ship_data.groupby('imo')['seen_date'].max().reset_index()

    # Merge to get the lat/lon corresponding to the latest 'seen_date'
    latest_locations = pd.merge(latest_dates, filtered_ship_data, on=['imo', 'seen_date'], how='left')

    # Create a column 'hours_since_latest' representing the difference in hours from the latest 'seen_date'
    latest_locations['hours_since_latest'] = (latest_locations['seen_date'].max() - latest_locations['seen_date']).dt.total_seconds() / 3600

    # Create a new column 'size' to differentiate between latest and previous locations
    latest_locations['size'] = 10  # Default size for previous locations
    #latest_locations.loc[latest_locations['hours_since_latest'] == 0, 'size'] = 20  # Larger size for the latest location

    #filtered_ship_data = filtered_ship_data[filtered_ship_data['seen_date_hour'] <= selected_time_range]
    print("part 5")

    # Calculate counts of 'Full' and 'Empty' values in the 'ef' column
    full_count = len(latest_locations[latest_locations['ef'] == 0])  # Assuming '0' represents 'Full'
    empty_count = len(latest_locations[latest_locations['ef'] == 1])  # Assuming '1' represents 'Empty'
    total=full_count + empty_count

    yyfull_count = len(latest_locations[latest_locations['empty_full'] == 0])
    yyempty_count = len(latest_locations[latest_locations['empty_full'] == 1])
    yytotal=yyfull_count+yyempty_count
    
    # Create text to display the counts
    ef_counts_text = html.P(f' Full : {full_count}, Empty : {empty_count} ,total :{total}|| '
                        f'y/y - Full : {yyfull_count}, Empty : {yyempty_count},total :{yytotal}')
    #ef_counts_text= html.P(f'Full Count2:{yyfull_count}, Empty Count2: {yyempty_count}')

    print("part 6")
    
    # Get unique regions and assign a unique color to each region
    unique_regions = filtered_ship_data['region'].unique()
    color_map = {
        region: px.colors.qualitative.Set1[i % len(px.colors.qualitative.Set1)]
        for i, region in enumerate(unique_regions)
    }

    traces = []
    #color = 'Same Color'  # Set a common color for all traces
    print("part 7")
    for imo in filtered_ship_data['imo'].unique():
        imo_df = filtered_ship_data[filtered_ship_data['imo'] == imo]
        print("part 7.1")

        latest_time = filtered_ship_data['cumulative_hours'].max()
        start_hour = max(latest_time - selected_time_range, 0)
        print("part 7.2")

        imo_filtered = imo_df[(imo_df['cumulative_hours'] >= start_hour) & (imo_df['cumulative_hours'] <= latest_time)]

        print("part 8")

        customdata_columns = ['imo','region', 'subregion', 'port_name','model_eta', 'name', 'size','draft','max_draft','ef','stated_destination','stated_eta','begin_port_name','begin_region','origin_type','idle_y']  # Columns to include in customdata
    
            # Create hovertemplate dynamically based on columns
        hovertemplate = "<br>".join([f"<b>{col}</b>: %{{customdata[{i}]}}" for i, col in enumerate(customdata_columns)]) + "<extra></extra>"
    
            # Create customdata DataFrame dynamically based on columns
        customdata = pd.DataFrame({col: imo_df[col] for col in customdata_columns})

        #end_hour = imo_df['seen_date_hour'].max()
        #start_hour = max(end_hour - selected_time_range, 0)

        #imo_filtered = imo_df[(imo_df['seen_date_hour'] >= start_hour) & (imo_df['seen_date_hour'] <= end_hour)]

        print("part 9")
        
        imo_map_trace = go.Scattermapbox(
            mode="lines",
            lon=imo_filtered['lon'],
            lat=imo_filtered['lat'],
            marker={'size': 5},
            line=dict(color=color_map.get(imo_df['region'].iloc[0], 'white')),  # Assign color based on 'region'
            name=f'imo={imo}',
            hovertemplate=hovertemplate,
            customdata=customdata,
            showlegend=False
        )
        # Append each Scattermapbox trace to the 'traces' list
        traces.append(imo_map_trace)
    print("part 10")
    # Create a base map using plotly express scatter_mapbox
    imo_map = px.scatter_mapbox(
        latest_locations,
        lat='lat',
        lon='lon',
        zoom=2,
        width=1000,
        height=600,
        title=f'IMO and Ports Locations for {selected_regions if selected_regions else "All"}',
        color='region' , # Assuming 'region' column determines color in latest_locations
        color_discrete_map=color_map  # Apply the same color map to ensure consistency
    )

    
    imo_map.update_traces(marker=dict(size=15))

    print("part 11")
    
    # Update marker sizes for differentiating latest and previous locations
    #imo_map.update_traces(marker=dict(size=latest_locations['size']))
    imo_map.update_layout(mapbox_style="open-street-map", margin={"r": 0, "t": 0, "l": 0, "b": 0})

    # Add the traces to the `imo_map` object
    for trace in traces:
        imo_map.add_trace(trace)
    #imo_map.add_trace(fig_trace)

    # Add ports data to the map
    ports_map = px.scatter_mapbox(
        ports_data,
        lat='lat',
        lon='lon',
        zoom=2,
        width=1000,
        height=600,
        text='name',
        title='IMO and Ports Locations'
    )

    print("part 12")

    ports_map.update_traces(marker=dict(size=10, color='grey',opacity=0.8))

    for data in ports_map.data:
        imo_map.add_trace(data)

    imo_map.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0}
    )
    print("part 13")

    return imo_map,ef_counts_text

#fig.show()
if __name__ == '__main__':
    app.run_server(debug=True)

