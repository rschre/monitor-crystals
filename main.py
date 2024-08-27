import datetime

import plotly.express as px
from dash import Dash, Input, Output, State, callback, dcc, html
from pypylon import pylon

from camera_handling import (
    get_bgr_converter,
    get_camera,
    get_img_from_grab_result,
    grab_single_frame,
)

camera = get_camera()
converter = get_bgr_converter()

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    [
        html.H1("Capture Crystal Formation", style={"textAlign": "center"}),
        html.Div(id="live-update-text"),
        dcc.Graph(id="live-update-graph", style={"height": "80vw"}),
        dcc.Interval(
            id="interval-component",
            interval=15 * 1000,
            n_intervals=0,  # in milliseconds
        ),
    ],
    style={"padding": "20px", "textAlign": "left"},
)


@app.callback(
    Output("live-update-text", "children"), Input("interval-component", "n_intervals")
)
def update_text(n):
    style = {"padding": "5px", "fontSize": "16px"}
    return [
        html.Span(
            f'Last capture triggered at: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            style=style,
        ),
    ]


@app.callback(
    Output("live-update-graph", "figure"),
    Input("interval-component", "n_intervals"),
    State("live-update-graph", "figure"),
)
def update_graph(n, fig):
    grabResult = grab_single_frame(camera)
    img = get_img_from_grab_result(grabResult, converter)

    fig = px.imshow(img, title=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return fig


if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
