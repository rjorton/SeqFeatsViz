import base64
import io
import json
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import time
import re

app = dash.Dash()
# For testing vv
pd.set_option('display.expand_frame_repr', False)
app.css.config.serve_locally = False
app.css.append_css({'external_url': 'https://codepen.io/amyoshino/pen/jzXypZ.css'})
# CSS is taken from this video https://www.youtube.com/watch?v=f2qUWgq7fb8&feature=youtu.be and app layout is somewhat similar.

app.layout = html.Div([
    html.Div(id="hidden_data", style={'display': 'none'}),
    html.Div(id="hidden_header", style={'display': 'none'}),
    html.Div([
        html.Div([
           html.H3(
               children='SeqFeatsViz'
           ),
           html.P(
               children='Interactive visualisation of virus dinucleotide biases using python / dash.'
           )
        ], className='seven columns'),
        html.Div([
            html.H6(
                children='Known issues:'
            ),
            html.P(
                children='- Toggling series in the legend may cause points to disappear with datasets > 10k points.'

            ),
            html.P(
                children='- You need to double click the graph to unselect data, clear table won\'t suffice'
            )
        ], className='five columns', style={'align': 'right', 'font-size': '8pt'})
     ], style={'background-color': '#E6E6E6', 'border-style': 'solid', 'border-width': '2px'}, className='row'),
    html.Div([
        html.Div([
            html.Label('Field Separator'),
            dcc.Dropdown(
                id='sep_drop',
                options=[
                    {'label': 'TSV', 'value': 'tab_sep'},
                    {'label': 'CSV', 'value': 'comma_sep'}
                ],
                value='tab_sep'
            )
        ], className='two columns'),
        html.Div([
            html.Label('Header Row'),
            dcc.Dropdown(
                id='header_drop',
                options=[
                    {'label': 'Yes', 'value': 'header_1'},
                    {'label': 'No', 'value': 'header_0'}
                ],
                value='header_1'
            )
        ], className='two columns'),
        html.Div([
           dcc.Upload(
            id="csv-upload",
            children=html.Div([
                "Drag and drop or", html.A(" Select File")
            ]),
            className='three columns',
            style={
               'height': '100%',
               'width': '25%',
               'float': 'right',
               'position': 'relative',
               'borderWidth': '1px',
               'borderStyle': 'dashed',
               'borderRadius': '5px',
               'textAlign': 'center',
               'margin': '30px',
               'background-color': '#FEFEFE'
            },
           )
        ], id='hidden_upload', style={'visibility': 'hidden'})
    ], className='row'),
    #
    html.Div([
        html.Div([
            html.Label('X-Values'),
            dcc.Dropdown(
                id='xaxis_drop'
            )
        ], className='two columns'),
        html.Div([
            html.Label('Y-Values'),
            dcc.Dropdown(
                id='yaxis_drop'
            )
        ], className='two columns'),
        html.Div([
            html.Label('Series'),
            dcc.Dropdown(
                id='series_drop'
            )
        ], className='two columns'),
        html.Div([
            html.Label('Filter Column'),
            dcc.Dropdown(
                id='filter_drop'
            )
        ], className='two columns'),
        html.Div([
            html.Label('Filter Value'),
            dcc.Dropdown(
                id='filter_value'
            )
        ], className='two columns')
    ], id='main_div', style={'visibility': 'hidden'}, className='row'),
    #
    html.Div([
        html.Div([
            html.Label('GenBank-Accession'),
            dcc.Dropdown(
                id='genbank_drop',
                value="N/A"
            )
        ], id='genbank_div', className='two columns'),
        html.Div([
            html.Label('Ensembl-ID'),
            dcc.Dropdown(
                id='ensembl_drop',
                value="N/A"
            )
        ], id='ensembl_div', className='two columns'),
        html.Div([
            html.Label('Log axes'),
            dcc.Dropdown(
                id='log_drop'
            )
        ], className='two columns'),
        html.Div([
            html.Label('Sort numerical'),
            dcc.Dropdown(
                id='sort_drop'
            )
        ], className='two columns'),
        html.Div([
            html.Label('Search-In'),
            dcc.Dropdown(
                id='searchin_drop',
                multi=True
            )
        ], className='four columns'),
    ], id='main_div2', style={'visibility': 'hidden'}, className='row'),
    #
    html.Div([
        html.Div([
            dcc.Graph(
                id="Scatter-Graph"
            )
        ], className='twelve columns')
    ], style={'border-style': 'solid', 'border-width': '2px', 'margin-top': '5px'}, className='row'),
    html.Div([
        html.Div([
            html.Label('Search graph:',
                       style={'text-align': 'center',
                              'margin-top': '5px'})
        ], className='two columns'),
        html.Div([
            dcc.Input(
                id='search_box',
                style={
                    'width': '100%',
                    'height': '100%',
                    'padding-top': '18px',
                    'font-size': '12px',
                    'margin-top': '2px'
                }
            )
        ], className='three columns'),
        html.Div([
            html.Button(
                'Search',
                id='search_button',
                style={'margin-top': '2px', 'background-color': '#FEFEFE'}
            )
        ], className='two columns'),
        html.Div([
            html.Button(
                'Clear',
                id='clear_search',
                style={
                    'margin-top': '2px',
                    'background-color': '#FEFEFE'
                }
            )
        ], className='two columns'),
        html.Div([
            html.Button(
                'Clear Table',
                id='clear_button',
                style={
                    'margin-top': '2px',
                    'background-color': '#FEFEFE'
                }
            )
        ], className='two columns')
    ], style={'background-color': '#E6E6E6', 'border-style': 'solid', 'border-top-style': 'none', 'border-width': '2px', 'padding-bottom': '10px'}, className='row'),
    html.Div([
        html.Div([], style={'margin-top': '10px', 'background-color': '#E6E6E6', 'border-style': 'solid', 'border-width': '2px', 'visibility': 'none'}, className='twelve columns', id='dtable_div')
    ], className='row')
])


# Function to pull a dataframe from a user uploaded csv or tsv
def parse_csv(contents, filename, sep_radio, header):
    # Don't do anything if the variables aren't set
    if contents is None:
        exit(1)
    if sep_radio is None:
        exit(1)

    cont_sep = ","
    if sep_radio == "comma_sep":
        cont_sep = ","
    elif sep_radio == "tab_sep":
        cont_sep = "\t"

    # this does not split the data, but splits the file info - so always ,
    content_type, content_string = contents.split(",")
    # Decode the file
    decoded = base64.b64decode(content_string)

    # Make a data frame with pandas
    if header == "header_1":
        df = pd.read_csv(io.StringIO(decoded.decode('utf8')), header=0, sep=cont_sep)
    else:
        df = pd.read_csv(io.StringIO(decoded.decode('utf8')), header=None, sep=cont_sep)
        # If there is no header make a new header like this: Column 1 Column 2 etc, etc
        df.columns = ["Column " + str(i) for i in range(1, len(df.columns.values) + 1)]

    return df

# Call back to update hidden & show drop downs
# Can't currently add clickable links to dash datatables see:
# https://github.com/plotly/dash-table-experiments/pull/11


# Populate values in SearchIn into Ensembl if SearchIn changes
@app.callback(
    Output('ensembl_drop', 'options'),
    [Input('searchin_drop', 'value')]
)
def update_ensemble(drop):
    if drop is None or len(drop) == 0:
        # return []
        exit(1)
    else:
        return [{'label': i, 'value': i} for i in drop]

# Removed the show_ensembl call back as not needed?


# Populate values in SearchIn into Genbank if SearchIn changes
@app.callback(
    Output('genbank_drop', 'options'),
    [Input('searchin_drop', 'value')]
)
def update_genbank(drop):
    if drop is None or len(drop) == 0:
        # return []
        exit(1)
    else:
        return [{'label': i, 'value': i} for i in drop]


# Removed the show_ncbi callback as not needed?


# Show file upload button if header & separator are set
@app.callback(
    Output('hidden_upload', 'style'),
    [Input('sep_drop', 'value'),
     Input('header_drop', 'value')]
)
def show_upload(v1, v2):
    if v1 is None or v2 is None:
        return {'visibility': 'hidden'}
    else:
        return {'visibility': 'visible'}


# Parse the data file when upload button/select file hit
@app.callback(
    Output('hidden_data', 'children'),
    [Input("csv-upload", "contents"), Input("csv-upload", "filename")],
    [State("sep_drop", 'value'), State("header_drop", 'value')]
)
def get_file(file_contents, file_name, separator, header):
    df = parse_csv(file_contents, file_name, separator, header)
    # Read the csv and save it in the hidden div as json.
    return df.to_json(date_format='iso', orient='split')


# RJO - Not sure what exactly - must be using header names for dropdown values
@app.callback(
    Output('hidden_header', 'children'),
    [Input('hidden_data', 'children')]
)
def store_headers(data):
    if data is None:
        exit(1)
    else:
        df = (pd.read_json(data, orient='split'))
        return json.dumps(list(df.columns.values))


# Callback to show main_div (x-axis, y-axis etc) after successful file upload
@app.callback(
    Output('main_div2', 'style'),
    [Input('hidden_data', 'children')]
)
def show_under_main(data):
    return {'background-color': '#E6E6E6', 'border-style': 'solid', 'border-top-style': 'none', 'border-width': '2px', 'visibility': 'visible'}


# Callback to show main_div2 (ensembl, genbank etc) after successful file upload
@app.callback(
    Output('main_div', 'style'),
    [Input('hidden_data', 'children')]
)
def show_main_div(data):
    return {'background-color': '#E6E6E6', 'border-style': 'solid', 'border-bottom-style': 'none', 'border-width': '2px', 'visibility': 'visible'}


# Series - update??
@app.callback(
    Output('searchin_drop', 'options'),
    [Input('hidden_header', 'children')]
)
def update_multi(data):
    name = json.loads(data)

    name.append("N/A")
    return [{'label': i, 'value': i} for i in name]


# Searchin - initial?
@app.callback(
    Output('searchin_drop', 'value'),
    [Input('hidden_header', 'children')]
)
def update_searchin(data):
    names = json.loads(data)
    return [i for i in names[3:] if i.lower().startswith("desc") or i.lower().startswith("ensembl") or i.lower().startswith("genbank") or i.lower().startswith("accession")]


# XAXIS
# This call back and all the other dropdown updates follow the same workflow as this.
@app.callback(
    Output('xaxis_drop', 'options'),
    [Input('hidden_header', 'children')]

)
def update_x_drop(data):
    # Decode the json dataframe which was stored on users browser.
    names = json.loads(data)
    # For each column header make it a drop down option.
    return [{'label': i, 'value': i} for i in names]


# XAXIS Initial call sets to [0]
@app.callback(
    Output('xaxis_drop', 'value'),
    [Input('hidden_header', 'children')]
)
def update_x_value(data):
    names = json.loads(data)
    return names[0]


# YAXIS
@app.callback(
    Output('yaxis_drop', 'options'),
    [Input('hidden_header', 'children')]
)
def update_y_drop(data):
    names = json.loads(data)
    return [{'label': i, 'value': i} for i in names]


# YAXIS Initial call sets to [1]
@app.callback(
    Output('yaxis_drop', 'value'),
    [Input('hidden_header', 'children')]
)
def update_x_value(data):
    names = json.loads(data)
    return names[1]


# Filter column/drop - no intial value set
@app.callback(
    Output('filter_drop', 'options'),
    [Input('hidden_header', 'children')]
)
def update_spec_drop(data):
    names = json.loads(data)
    return [{'label': i, 'value': i} for i in names]


# Filter value (from within the filter column) - no intial value set
@app.callback(
    Output('filter_value', 'options'),
    [Input('filter_drop', 'value'),
     Input('hidden_data', 'children')]
)
def update_spec_graph(val, data):
    df = pd.read_json(data, orient='split')
    if val is None:
        exit(1)
    return [{'label': i, 'value': i} for i in df[val].unique()]


# Series
@app.callback(
    Output('series_drop', 'options'),
    [Input('hidden_header', 'children')]
)
def update_cat_drop(data):
    names = json.loads(data)
    names.append("N/A")
    return [{'label': i, 'value': i} for i in names]


# Series Initial call sets to [2]
@app.callback(
    Output('series_drop', 'value'),
    [Input('hidden_header', 'children')]
)
def update_x_value(data):
    names = json.loads(data)
    return names[2]


# Log axes, x, y, x&y, reset
@app.callback(
    Output('log_drop', 'options'),
    [Input('xaxis_drop', 'value'),
     Input('yaxis_drop', 'value')]
)
def update_logs(x, y):
    if x is None or y is None:
        exit(1)
    names = [x, y]
    x_y = x + " + " + y
    names.append(x_y)
    names.append("Reset Axes")

    return [{'label': i, 'value': i} for i in names]


# Sort axes, x or y, or rest
@app.callback(
    Output('sort_drop', 'options'),
    [Input('xaxis_drop', 'value'),
     Input('yaxis_drop', 'value')]
)
def update_numeric(x, y):
    if x is None or y is None:
        exit(1)
    names = [x, y, "Reset Axes"]

    return [{'label': i, 'value': i} for i in names]


# Callback to update graph
@app.callback(
    Output('Scatter-Graph', 'figure'),
    [Input('xaxis_drop', 'value'),
     Input('yaxis_drop', 'value'),
     Input('series_drop', 'value'),
     Input('hidden_data', 'children'),
     Input('searchin_drop', 'value'),
     Input('search_button', 'n_clicks'),
     Input('log_drop', 'value'),
     Input('sort_drop', 'value'),
     Input('filter_value', 'value'),
     Input('clear_search', 'n_clicks_timestamp')],
    [State('search_box', 'value'),
     State('filter_drop', 'value')]
)
# Gets input values from all of the drop down menus - Updates when any of these values are changed.
def update_graph(xaxis, yaxis, series, hidden, mval, search_button, logs, nums, filter_val, clear_time, search, filter_col):
    # If any of the three values are not set don't do anything.
    if xaxis is None or yaxis is None or mval is None:
        exit(1)

    # Redraw the graph if the user hits the clear button.
    if clear_time is not None:
        if int(clear_time / 1000) == int(time.time()):
            search = ""

    # Read the json dataframe stored in the users browser.
    df = pd.read_json(hidden, orient='split')
    if filter_val is None:
        df = df
    else:
        df = df[df[filter_col] == filter_val]

    df_list = []

    to_search = True
    if search == "":
        to_search = False

    # For the search functionallity vv
    if search is not None and "N/A" not in mval and to_search:
        for i in mval:
            # Treat each column the user has chose in the text dropdown
            # As a column to search string for.
            # Partial string search using Pandas.
            df_list.append(df[df[i].str.contains(search, flags=re.IGNORECASE, na=False)])

        # You get separate dataframes for each separate text column so concat them together.
        # RJO - What if same entry appears in each frame?? multiple rows of same entry
        df = pd.concat(df_list)

    # Functions to deal with log scaling the plots. Both follow the same logic
    def logs_x(lst, x, y, n):
        if n == x or n is None or n == "Reset Axes":
            not_num = True
        else:
            not_num = False
        # If the log transform dropdown doesnt exists of the user selects reset axes
        # Don't do anything to the axis other than name it.
        if lst is None or len(lst) == 0 or "Reset Axes" in lst:
            if not_num:
                return {'title': str(x)}
            else:
                return {'title': "Rank"}

        # If theyve selected to log x axis or x and y axis
        # tell go.Layout that you want to log.
        else:
            if x in lst or str(x + " + " + y) in lst:
                if not_num:
                    return {'type': 'log', 'title': str(x)}
                else:
                    return {'type': 'log', 'title': "Rank"}
            else:
                if not_num:
                    return {'title': str(x)}
                else:
                    return {'title': "Rank"}

    def logs_y(lst, x, y, n):
        if n == y or n is None or n == "Reset Axes":
            not_num = True
        else:
            not_num = False

        if lst is None or len(lst) == 0 or "Reset Axes" in lst:
            if not_num:
                return {'title': str(y)}
            else:
                return {'title': "Rank"}
        else:
            if y in lst or str(x + " + " + y) in lst:
                if not_num:
                    return {'type': 'log', 'title': str(y)}
                else:
                    return {'type': 'log', 'title': "Rank"}
            else:
                if not_num:
                    return {'title': str(y)}
                else:
                    return {'title': "Rank"}

    def nums_df(string, axis, frame):
        if string == axis:
            return frame[axis].sort_values(ascending=False)
        elif string == "Reset Axes" or string is None:
            return frame[axis]
        else:
            data = []
            for en, i in enumerate(frame[axis]):
                data.append(en)
            df = pd.DataFrame(data)
            return df.iloc[:, 0]

    # If the user hasn't specified a series colum in the drop down do this
    if series == "N/A" or series is None:
        traces = []
        # If user has specified text columns do this.
        if "N/A" not in mval:
            traces.append(go.Scattergl(
                # X-coords
                y=nums_df(nums, yaxis, df),
                # Y-Coords
                x=nums_df(nums, xaxis, df),
                # Separate df for each text column to values
                text=df[[i for i in mval]].values.tolist(),
                mode="markers",
                opacity=0.4
            ))
        else:
            traces.append(go.Scattergl(
                y=nums_df(nums, yaxis, df),
                x=nums_df(nums, xaxis, df),
                text="",
                mode="markers",
                opacity=0.4
            ))
        return {
            'data': traces,
            'layout': go.Layout(
                xaxis=logs_x(logs, xaxis, yaxis, nums),
                yaxis=logs_y(logs, xaxis, yaxis, nums),
                hovermode='closest'
            )
        }
    # y = subset_df[yaxis],
    # x = subset_df[xaxis],
    # If the user has specified some categories do this.
    else:
        traces = []
        # For each unique item in the series column the user has specfied
        # subset the dataframe to rows with this value.
        for i in df[series].unique():
            subset_df = df[df[series] == i]

            # If there's is text specified do the same as we did above.
            if "N/A" not in mval:
                traces.append(
                    go.Scattergl(
                        y=nums_df(nums, yaxis, subset_df),
                        x=nums_df(nums, xaxis, subset_df),
                        text=subset_df[[i for i in mval]].values.tolist(),
                        mode='markers',
                        name=str(i),
                        opacity=0.4
                    )
                )

            # If there's no text specified just leave the element blank.
            else:
                traces.append(
                    go.Scattergl(
                        y=nums_df(nums, yaxis, subset_df),
                        x=nums_df(nums, xaxis, subset_df),
                        text="",
                        mode='markers',
                        name=str(i),
                        opacity=0.4
                    )
                )

        return {
            'data': traces,
            'layout': go.Layout(
                xaxis=logs_x(logs, xaxis, yaxis, nums),
                yaxis=logs_y(logs, xaxis, yaxis, nums),
                hovermode='closest'
            )
        }


# Callback to update table
@app.callback(
    Output('dtable_div', 'children'),
    [Input('Scatter-Graph', 'clickData'), Input('Scatter-Graph', 'selectedData')],
    [State('searchin_drop', 'value'),
     State('xaxis_drop', 'value'),
     State('yaxis_drop', 'value'),
     State('ensembl_drop', 'value'),
     State('genbank_drop', 'value')]
)
# Update the table with data from either / both of a box / lassoo select or a click.
def update_table(clicked, selected,  mval, xval, yval, ensembl, genbank):

    # A funciton to populate a table and add hyper links into it.
    def table(frame, eb, nc, xaxis):
        # Store all the row data as we need to return it
        rows = []
        frame = frame.sort_values(xaxis, ascending=False)
        # For each row in the dataframe
        for i in range(len(frame)):

            # Store each row in memory
            row = []
            for col in frame.columns:
                # For each column make a value as this row/col in the df
                value = frame.iloc[i][col]

                # If the column in the df is the one the user stated as the ensembl col
                # make it a hyper link.
                # Same goes for genbank.
                if col == eb:
                    # value = value.replace("'", "")
                    cell = html.Td(
                        html.A(
                            href="https://www.ensembl.org/Multi/Search/Results?q="+value+";site=ensembl_all", target='_blank', children=value)
                    )
                elif col == nc:
                    cell = html.Td(
                        html.A(
                            href="https://www.ncbi.nlm.nih.gov/nuccore/"+value, target='_blank', children=value
                        )
                    )
                # If its not an ensembl or genbank column dont add a hyper link.
                else:
                    cell = cell = html.Td(children=value)
                # Append cell values to the row
                row.append(cell)
            # append row values to the row
            rows.append(html.Tr(row))

        # Return the formatted html table.
        return html.Table(
            [html.Tr([html.Th(col) for col in df.columns])] + rows
        )

    if clicked is None and selected is None:
        exit(1)

    # If they;ve used the box tool do this.
    if selected is not None:
        coords = json.dumps(selected, indent=2)
        coords = json.loads(coords)

        # Make a simple data frame of all the x and y coords
        xlist = []
        ylist = []
        for i in coords['points']:
            xlist.append(i['x'])
            ylist.append(i['y'])

        data = {str(xval): xlist, str(yval): ylist}
        df = pd.DataFrame(data=data)

        # If there;s no extra data columns we can return at this point.
        if "N/A" in mval:
            return table(df, ensembl, genbank, xval)

        # If there is text. For the json of EACH point look at specific indices for the
        # correct text to print to screen.
        # We know the json will only store what we need, so if we enumerate the cols we know
        # exactly where to look.
        # i.e user specifies cols: 8,10,12
        # we enumerate this to indices 0,1,2
        # So we look in the json for ['points'][0], etc
        # This same procedure is followed for the click data, just a lot simpler.
        val_dict = {}
        for i in coords['points']:
            for en, j in enumerate(mval):
                key = str(j)
                val_dict.setdefault(key, [])
                try:
                    val_dict[key].append(i['text'].split("',")[en].replace("]", "").replace("[", "").replace("'", ""))
                except IndexError:
                    val_dict[key].append(i['text'].split(",")[en].replace("]", "").replace("[", "").replace("'", ""))

        for i in val_dict:
            df[str(i)] = val_dict[i]
        return table(df, ensembl, genbank, xval)

    else:
        coords = json.dumps(clicked, indent=2)
        coords = coords.replace("[", "").replace("]", "")
        coords = json.loads(coords)
        xcoord = coords['points']['x']
        ycoord = coords['points']['y']
        data = {str(xval): [xcoord], str(yval): [ycoord]}
        df = pd.DataFrame(data=data)
        if "N/A" in mval:
            return table(df, ensembl, genbank, xval)
        for en, i in enumerate(mval):
            try:
                df[str(i)] = coords['points']['text'].split("',")[en].replace("'", "")
            except IndexError:
                df[str(i)] = coords['points']['text'].split(",")[en].replace("'", "")

        return table(df, ensembl, genbank, xval)


# Callbacks to clear table
# Really janky way to clear the table.
@app.callback(
    Output('dtable_div', 'style'),
    [Input('Scatter-Graph', 'clickData'),
     Input('Scatter-Graph', 'selectedData'),
     Input('clear_button', 'n_clicks_timestamp')]
)
def clear_table(click, select, button):
    if button is None:
        exit(1)
    # If the time the button is pressed = current time clear table.
    if int(button / 1000) == int(time.time()):
        return {'visibility': 'hidden'}
    else:
        return {'margin-top': '10px',
                'background-color': '#E6E6E6',
                'border-style': 'solid',
                'border-width': '2px',
                'visibility': 'visible'}



# Callbacks to clear search bar
@app.callback(
    Output('search_box', 'value'),
    [Input('clear_search', 'n_clicks')]
)
def clear_search(button):
    if button == 0:
        exit(1)
    return ""


if __name__ == '__main__':
    app.run_server(debug=False)
