import datetime

import numpy as np
import plotly.express as px
from dash import Dash, Input, Output, State, callback, dcc, html
from pypylon import pylon
from segment_anything import SamAutomaticMaskGenerator, sam_model_registry

from camera_handling import (
    get_bgr_converter,
    get_camera,
    get_img_from_grab_result,
    grab_single_frame,
)

camera = get_camera()
converter = get_bgr_converter()

sam_checkpoint = "sam_vit_h_4b8939.pth"
model_type = "vit_h"

sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
mask_generator = SamAutomaticMaskGenerator(sam)

external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    [
        html.H1("Capture Crystal Formation", style={"textAlign": "center"}),
        html.Div(id="live-update-text"),
        dcc.Graph(id="live-update-graph", style={"height": "40vw"}),
        dcc.Graph(id="annotated-graph", style={"height": "40vw"}),
        dcc.Interval(
            id="interval-component",
            interval=60 * 1000,
            n_intervals=0,  # in milliseconds
        ),
    ],
    style={"padding": "20px", "textAlign": "left"},
)


def show_annotations(anns):
    sorted_anns = sorted(anns, key=(lambda x: x["area"]), reverse=True)

    img = np.ones(
        (
            sorted_anns[0]["segmentation"].shape[0],
            sorted_anns[0]["segmentation"].shape[1],
            4,
        )
    )
    img[:, :, 3] = 0
    for ann in sorted_anns:
        m = ann["segmentation"]
        color_mask = np.concatenate([np.random.random(3), [0.35]])
        img[m] = color_mask

    return img


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

    mask = mask_generator.generate_mask(img)
    anns = mask_generator.segment(mask)

    fig = px.imshow(anns, title=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return fig


if __name__ == "__main__":
    app.run_server(debug=True, port=8050)
