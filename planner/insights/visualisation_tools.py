from datetime import datetime, timezone, timedelta
from tzlocal import get_localzone
import pandas

import matplotlib
import matplotlib.dates as mdates
from matplotlib.ticker import AutoMinorLocator

from bokeh.plotting import figure
from bokeh.models import Span
from bokeh.embed import components

from planner.insights.data_tools import format_short_date_range

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


def plot_png(dfs: list[pandas.DataFrame],
             square_lines: bool = True,
             show_now_marker: bool = True,
             end_marker: datetime = None,
             starts_and_stops: list[tuple[datetime, datetime]] = None,
             ):

    # Debugging variable that allows one to see an interactive matplotlib plot.
    # For normal behaviour, leave as True.
    return_file = True

    line_colours = ["b-", "y-", "r-", "g-"]

    if return_file:
        matplotlib.use('AGG')
    else:
        matplotlib.use('macosx')

    import matplotlib.pyplot as plt

    plt.figure()
    ax = plt.gca()
    ax.grid(which='both')

    if show_now_marker:
        now = datetime.now(tz=get_localzone())
        plt.axvline(x=now, color='pink', linestyle='-.')

    if starts_and_stops:
        for start, stop in starts_and_stops:
            plt.axvline(x=start.astimezone(get_localzone()), color='green', linestyle=':')
            plt.axvline(x=stop.astimezone(get_localzone()), color='red', linestyle=':')

    if end_marker is not None:
        assert end_marker.tzinfo, "end must be tz aware"
        end_marker = end_marker.astimezone(timezone.utc)
        plt.axvline(x=end_marker, color='pink', linestyle='-.')

    # ToDo: This is horribly repetitive and needs tidying up.

    i = 0
    min_date = None
    max_date = None
    for df in dfs:
        if min_date is None or min_date > df.index.min():
            min_date = df.index.min()
        if max_date is None or max_date < df.index.max():
            max_date = df.index.max()
        if square_lines:
            endpoints = pandas.DataFrame(df.values,
                                         index=df.index + timedelta(minutes=29, seconds=59),
                                         columns=df.columns)
            df = df.append(endpoints).sort_index()

        plt.plot(df.index.map(lambda x: x.astimezone(get_localzone())),
                 df[df.columns[0]].values.tolist(),
                 line_colours[i],
                 label=df.columns[0])
        i += 1

        ax = plt.gca()
        ax.grid(which='both')
        ax.grid(which='minor')

    ax = plt.gca()
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%a %d', tz=get_localzone()))
    ax.xaxis.set_minor_locator(mdates.HourLocator(interval=3))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%H', tz=get_localzone()))
    ax.tick_params(which='both', width=1)
    ax.tick_params(which='major', length=10)
    ax.tick_params(which='minor', length=2)

    date_range = format_short_date_range((min_date, max_date))
    plt.title(f"Energy Prices from {date_range}")
    plt.xlabel("Price (p/kWh)")
    ax.legend()

    if return_file:
        plt.savefig("figure.png")
        with open("figure.png", "rb") as f:
            png_data = f.read()
        return png_data
    else:
        plt.show()
