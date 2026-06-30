from posixpath import basename

from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

import dash_bootstrap_components as dbc  # type: ignore

default_columns = (
    "Run,Type,Name,Request Count,Failure Count,Median Response Time,"
    "Average Response Time,Min Response Time,Max Response Time,"
    "Average Content Size,Requests/s,Failures/s,50%,66%,75%,80%"
    ",90%,95%,98%,99%,99.9%,99.99%,100%".split(",")
)
benchmark_df1 = pd.DataFrame([], columns=default_columns)
benchmark_df2 = pd.DataFrame([], columns=default_columns)


def gen_plot(df, df2):
    df_fin = pd.concat([df, df2], ignore_index=True)
    df_fin["Name"] = df_fin["Name"].str.split("|").str[-1]
    return px.bar(df_fin, x="Name", y="Median Response Time", barmode="group", color="Run")


def upload_form(id_div):
    return dcc.Upload(
        id=id_div,
        children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
        style={
            "width": "100%",
            "height": "60px",
            "lineHeight": "60px",
            "borderWidth": "1px",
            "borderStyle": "dashed",
            "borderRadius": "5px",
            "textAlign": "center",
            "margin": "10px",
        },
    )


app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = [
    html.Div(
        className="container",
        children=[
            html.H1(children="Performance comparison", style={"textAlign": "center"}),
            html.Div(
                className="row",
                children=[
                    html.Div(
                        className="col-6",
                        children=[
                            html.H2("Run 1", className="title"),
                            upload_form("upload-perf1"),
                        ],
                    ),
                    html.Div(
                        className="col-6",
                        children=[
                            html.H2("Run 2", className="title"),
                            upload_form("upload-perf2"),
                        ],
                    ),
                    html.Div(
                        className="col-12",
                        children=[
                            dcc.Graph(
                                id="graph-content",
                                figure=gen_plot(benchmark_df1, benchmark_df2),
                            )
                        ],
                    ),
                ],
            ),
        ],
    ),
]


@callback(
    Output("graph-content", "figure"),
    Input("upload-perf1", "filename"),
    Input("upload-perf2", "filename"),
)
def update_graph(value, value2):
    global benchmark_df1, benchmark_df2
    if value is not None:
        benchmark_df1 = pd.read_csv(value)
        benchmark_df1["Run"] = basename(value)
    if value2 is not None:
        benchmark_df2 = pd.read_csv(value2)
        benchmark_df2["Run"] = basename(value2)
    return gen_plot(benchmark_df1, benchmark_df2)


if __name__ == "__main__":
    app.run(debug=True)
