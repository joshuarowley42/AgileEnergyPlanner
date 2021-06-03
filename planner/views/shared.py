from django.shortcuts import render

from planner.common import energy_planner
from planner.insights.data_tools import format_short_date, format_short_date_range
from planner.insights.visualisation_tools import plot_html


def index(request):
    # Get Gas and Electric Prices
    ep_pd = energy_planner.ep_df_from_now()
    gp_pd = energy_planner.gp_df_from_now()

    # Get best stop & start times for Electric usage.
    best_starts_and_stops, best_price = energy_planner.plan_usage_periods(hours=3, mode="best")
    peak_starts_and_stops, peak_price = energy_planner.plan_usage_periods(hours=3, mode="peak")

    # Get an HTML graph of the same

    now_ep = ep_pd.values[0][0]
    now_time = format_short_date(ep_pd.index[0])
    best_time = format_short_date_range(best_starts_and_stops[0])
    peak_time = format_short_date_range(peak_starts_and_stops[0])
    average = energy_planner.average_price()
    average_excluding_peak = energy_planner.average_price(excluded_periods=peak_starts_and_stops)

    graph = plot_html([ep_pd, gp_pd], starts_and_stops=best_starts_and_stops + peak_starts_and_stops)
    price_data = [("Current Price", now_time, f"{now_ep:.2f}"),
                  ("Best 3h", best_time, f"{best_price:.2f}"),
                  ("Peak 3h", peak_time, f"{peak_price:.2f}"),
                  ("Average", "all-day", f"{average:.2f}"),
                  ("Average", "outside peak", f"{average_excluding_peak:.2f}")]

    return render(request, 'index.html', context={"graph": graph,
                                                  "price_data": price_data})