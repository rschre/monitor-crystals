from dash import Dash, Input, Output, State, callback, dcc, html

from camera_handling import (
    get_bgr_converter,
    get_camera,
    get_img_from_grab_result,
    grab_single_frame,
)

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    [
        html.H1("Capture Crystal Formation", style={"textAlign": "center"}),
        # capture interval and start button
        html.Div(
            [
                html.Div(
                    [
                        html.Label("Capture Interval (s)"),
                        dcc.Input(
                            id="interval",
                            type="number",
                            value=1,
                            style={"width": "100%"},
                        ),
                    ],
                    style={"width": "50%"},
                ),
                html.Div(
                    [
                        html.Button("Start", id="start", n_clicks=0),
                        html.Button("Stop", id="stop", n_clicks=0),
                    ],
                    style={"width": "50%"},
                ),
            ],
            style={"display": "flex"},
        ),
        html.Div(
            [
                dcc.Graph(
                    id="image",
                    style={"width": "100%", "height": "100%"},
                    config={"displayModeBar": False},
                )
            ],
        ),
    ]
)


# callback to update the image, this is where the camera handling code will go
@callback(
    Output("image", "figure"),
    Input("start", "n_clicks"),
    Input("stop", "n_clicks"),
    State("interval", "value"),
)
def update_image(start, stop, interval):
    if start > stop:
        camera = get_camera()
        converter = get_bgr_converter()
        grabResult = grab_single_frame(camera)
        img = get_img_from_grab_result(grabResult, converter)
        return {
            "data": [{"z": img}],
            "layout": {
                "xaxis": {"visible": False},
                "yaxis": {"visible": False},
                "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
            },
        }
    else:
        return {
            "data": [{"z": [[0]]}],
            "layout": {
                "xaxis": {"visible": False},
                "yaxis": {"visible": False},
                "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
            },
        }
