
import matplotlib
import matplotlib.dates as mdates
from matplotlib.ticker import AutoMinorLocator
from datetime import datetime, timezone, timedelta
import pandas

from bokeh.plotting import figure, show
from bokeh.models import Span
from bokeh.models.formatters import DatetimeTickFormatter
from bokeh.resources import CDN
from bokeh.embed import file_html

from config import *


def show_plot(gp=None, ep=None,
              gu=None, eu=None,
              show_now_marker=False, end_marker: datetime = None,
              starts_and_stops=None, square_lines=True,
              return_file=False):

    """
    A very messy function to generate graphs, and either show them on the screen, or create a png.

    :param gp: Gas Prices Dict
    :param ep: Electricity Prices Dict
    :param gu: Gas Usage Dict
    :param eu: Electricity Usage Dict
    :param show_now_marker: Show a vertical line on the graph for now
    :param end_marker: Show vertical line on the graph for a given end_market
    :param starts_and_stops: List of (start, stop) datetime tuples. Will show on graph green & red.
    :param square_lines:
    Make the lines flat between period start and end. Otherwise it's a graph of
    prices at start-time which can be misleading.
    :param return_file: Return a png rather than displaying an interactive plot.
    :return:
    """

    if return_file:
        matplotlib.use('AGG')
    else:
        matplotlib.use('macosx')

    import matplotlib.pyplot as plt

    plt.figure()
    ax = plt.gca()
    ax.grid(which='both')

    if show_now_marker:
        now = datetime.now(tz=timezone.utc)
        now = datetime(year=now.year,
                       month=now.month,
                       day=now.day,
                       hour=now.hour,
                       minute=now.minute - (now.minute % 30),
                       tzinfo=timezone.utc)
        plt.axvline(x=now, color='pink', linestyle='-.')

    if starts_and_stops:
        for start, stop in starts_and_stops:
            plt.axvline(x=start, color='green', linestyle=':')
            plt.axvline(x=stop, color='red', linestyle=':')

    if end_marker is not None:
        assert end_marker.tzinfo, "end must be tz aware"
        end_marker = end_marker.astimezone(timezone.utc)
        plt.axvline(x=end_marker, color='pink', linestyle='-.')

    # ToDo: This is horribly repetitive and needs tidying up.
    if ep is not None:
        if square_lines:
            for k in list(ep.keys()):
                ep[k + timedelta(minutes=29, seconds=59)] = ep[k]
        prices_pd_ep = pandas.DataFrame.from_dict(ep, orient="index", columns=['electricity'])
        prices_pd_ep.plot(y=["electricity"], ax=ax)
        ax = plt.gca()
        ax.set_ylim(0, 40)

    if gp is not None:
        if square_lines:
            for k in list(gp.keys()):
                gp[k + timedelta(minutes=29, seconds=59)] = gp[k]
        prices_pd_gp = pandas.DataFrame.from_dict(gp, orient="index", columns=['gas'])
        prices_pd_gp.plot(y=["gas"], ax=ax)
        ax = plt.gca()
        ax.set_ylim(0, 40)

    if eu is not None:
        if square_lines:
            for k in list(eu.keys()):
                eu[k + timedelta(minutes=29, seconds=59)] = eu[k]
        prices_pd_eu = pandas.DataFrame.from_dict(eu, orient="index", columns=['electricity usage'])
        prices_pd_eu.plot(y=["electricity usage"], secondary_y=True, ax=ax)
        ax = plt.gca()
        ax.set_ylim(0, 2)

    if gu is not None:
        if square_lines:
            for k in list(gu.keys()):
                gu[k + timedelta(minutes=29, seconds=59)] = gu[k]
        prices_pd_gu = pandas.DataFrame.from_dict(gu, orient="index", columns=['gas usage'])
        prices_pd_gu.plot(y=["gas usage"], secondary_y=True, ax=ax)
        ax = plt.gca()
        ax.set_ylim(0, 2)

    ax = plt.gca()
    ax.grid(which='both')
    ax.grid(which='minor')

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%a %d %H%M', tz=TIMEZONE))
    ax.xaxis.set_minor_locator(AutoMinorLocator(n=3))
    ax.tick_params(which='both', width=1)
    ax.tick_params(which='major', length=7)
    ax.tick_params(which='minor', length=4)

    if return_file:
        plt.savefig("figure.png")
        with open("figure.png", "rb") as f:
            png_data = f.read()
        return png_data
    else:
        plt.show()


def plot_html(dfs: list[pandas.DataFrame],
              square_lines: bool = True,
              show_now_marker: bool = True,
              end_marker: datetime = None,
              starts_and_stops: list[tuple[datetime, datetime]] = None,
              ):

    plot = figure(x_axis_type='datetime')
    # plot.xaxis.formatter = DatetimeTickFormatter(days='%H')
    plot.xaxis.minor_tick_line_color = "red"

    line_colours = ["blue", "orange", "red", "green"]

    if show_now_marker:
        now = datetime.now(tz=timezone.utc)
        now = now.replace(minute=now.minute - (now.minute % 30))

        plot.add_layout(Span(location=now,
                             dimension='height', line_color='pink',
                             line_dash='dashed', line_width=1))

    if end_marker is not None:
        end_marker = end_marker.astimezone(timezone.utc)
        plot.add_layout(Span(location=end_marker,
                             dimension='height', line_color='pink',
                             line_dash='dashed', line_width=1))

    if starts_and_stops is not None:
        for start, stop in starts_and_stops:
            plot.add_layout(Span(location=start,
                                 dimension='height', line_color='green',
                                 line_dash='dashed', line_width=1))
            plot.add_layout(Span(location=stop,
                                 dimension='height', line_color='red',
                                 line_dash='dashed', line_width=1))

    i = 0
    for df in dfs:

        if square_lines:
            endpoints = pandas.DataFrame(df.values,
                                         index=df.index + timedelta(minutes=29, seconds=59),
                                         columns=df.columns)
            df = df.append(endpoints).sort_index()

        plot.line(df.index,
                  df[df.columns[0]].values.tolist(),
                  legend_label=df.columns[0],
                  color=line_colours[i % len(line_colours)])
        i += 1

    return file_html(plot, CDN)
