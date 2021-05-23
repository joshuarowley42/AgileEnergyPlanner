from datetime import datetime, timezone, timedelta
from tzlocal import get_localzone
import pandas

from bokeh.plotting import figure
from bokeh.io import export_svg
from bokeh.models import Span
from bokeh.embed import components

from config import *


def plot_html(dfs: list[pandas.DataFrame],
              square_lines: bool = True,
              show_now_marker: bool = True,
              end_marker: datetime = None,
              starts_and_stops: list[tuple[datetime, datetime]] = None,
              ):
    plot = figure(x_axis_type='datetime')
    plot.xaxis.minor_tick_line_color = "red"

    line_colours = ["blue", "orange", "red", "green"]

    if show_now_marker:
        now = datetime.now()

        plot.add_layout(Span(location=now.replace(tzinfo=None),
                             dimension='height', line_color='pink',
                             line_dash='dashed', line_width=1))

    if end_marker is not None:
        plot.add_layout(Span(location=end_marker.astimezone(get_localzone()).replace(tzinfo=None),
                             dimension='height', line_color='pink',
                             line_dash='dashed', line_width=1))

    if starts_and_stops is not None:
        for start, stop in starts_and_stops:
            plot.add_layout(Span(location=start.astimezone(get_localzone()).replace(tzinfo=None),
                                 dimension='height', line_color='green',
                                 line_dash='dashed', line_width=1))
            plot.add_layout(Span(location=stop.astimezone(get_localzone()).replace(tzinfo=None),
                                 dimension='height', line_color='red',
                                 line_dash='dashed', line_width=1))

    i = 0
    for df in dfs:
        if square_lines:
            endpoints = pandas.DataFrame(df.values,
                                         index=df.index + timedelta(minutes=29, seconds=59),
                                         columns=df.columns)
            df = df.append(endpoints).sort_index()

        plot.line(df.index.map(lambda x: x.astimezone(get_localzone()).replace(tzinfo=None)),
                  df[df.columns[0]].values.tolist(),
                  legend_label=df.columns[0],
                  color=line_colours[i % len(line_colours)])
        i += 1

    return components(plot)


def plot_svg(dfs: list[pandas.DataFrame],
             square_lines: bool = True,
             show_now_marker: bool = True,
             end_marker: datetime = None,
             starts_and_stops: list[tuple[datetime, datetime]] = None,
             ):
    plot = figure(x_axis_type='datetime')
    plot.xaxis.minor_tick_line_color = "red"

    line_colours = ["blue", "orange", "red", "green"]

    if show_now_marker:
        now = datetime.now()

        plot.add_layout(Span(location=now.replace(tzinfo=None),
                             dimension='height', line_color='pink',
                             line_dash='dashed', line_width=1))

    if end_marker is not None:
        plot.add_layout(Span(location=end_marker.astimezone(get_localzone()).replace(tzinfo=None),
                             dimension='height', line_color='pink',
                             line_dash='dashed', line_width=1))

    if starts_and_stops is not None:
        for start, stop in starts_and_stops:
            plot.add_layout(Span(location=start.astimezone(get_localzone()).replace(tzinfo=None),
                                 dimension='height', line_color='green',
                                 line_dash='dashed', line_width=1))
            plot.add_layout(Span(location=stop.astimezone(get_localzone()).replace(tzinfo=None),
                                 dimension='height', line_color='red',
                                 line_dash='dashed', line_width=1))

    i = 0
    for df in dfs:
        if square_lines:
            endpoints = pandas.DataFrame(df.values,
                                         index=df.index + timedelta(minutes=29, seconds=59),
                                         columns=df.columns)
            df = df.append(endpoints).sort_index()

        plot.line(df.index.map(lambda x: x.astimezone(get_localzone()).replace(tzinfo=None)),
                  df[df.columns[0]].values.tolist(),
                  legend_label=df.columns[0],
                  color=line_colours[i % len(line_colours)])
        i += 1

    export_svg(plot, filename="figure.svg")
    with open("figure.svg", "rb") as f:
        svg_data = f.read()

    return svg_data
