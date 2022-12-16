#!/usr/bin/env python

import numpy as np
import enum
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Tuple, Protocol, cast
import dateutil.parser
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import re

TIME_RE = re.compile(
    r"WAIT TIME (?P<more_or_less>more|less) than (?P<num_hours>\d+) hour"
)


class MoreOrLess(enum.Enum):
    More = enum.auto()
    Less = enum.auto()


def parse_time(raw_time: str) -> Tuple[int, MoreOrLess]:
    match = TIME_RE.search(raw_time)
    if not match:
        raise ValueError(f"cannot match line {raw_time}")

    num_hours = match.group("num_hours")
    if match.group("more_or_less") == "more":
        more_or_less = MoreOrLess.More
    elif match.group("more_or_less") == "less":
        more_or_less = MoreOrLess.Less
    else:
        raise ValueError
    return (int(num_hours), more_or_less)


def sanitise_location_name(name):
    return name.lower().replace(" ", "_").replace("'", "").replace("'", "").replace(",", "").replace("’", "")


def render_location_graph(location_name, entries, output_dir):
    fig, axis = plt.subplots()

    y_data = defaultdict(list)

    for entry in entries:
        date, num_hours, _ = entry
        dt = dateutil.parser.parse(date)
        hour = dt.hour
        y_data[hour].append(num_hours)

    avs = []
    stdevs = []
    for i in range(24):
        values = y_data.get(i)
        if values is None:
            if i == 0:
                # TODO
                avs.append(0)
                stdevs.append(0)
            else:
                avs.append(avs[i - 1])
                stdevs.append(stdevs[i - 1])
            continue

        mean_value = np.average(values)
        stdev_value = np.std(values)
        avs.append(mean_value)
        stdevs.append(stdev_value)

    axis.bar(x=np.arange(24), height=avs)

    sanitised_location_name = sanitise_location_name(location_name)
    output_filename = str(output_dir / f"{sanitised_location_name}.png")
    axis.set(xlabel="Hour", ylabel="Average wait time [hours]", title=location_name)
    fig.tight_layout()
    fig.savefig(output_filename)


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


with sqlite3.connect("res.db") as conn:
    conn.row_factory = dict_factory

    query = """
    select 
        _commit_at as date,
        item.location as location,
        d.wait_time as wait_time
    from item_version_detail as d
    join item on d._item = item._id;
    """
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()

per_location = defaultdict(list)
for row in rows:
    num_hours, more_or_less = parse_time(row["wait_time"])
    per_location[row["location"]].append((row["date"], num_hours, more_or_less))

output_dir = Path.cwd() / "plots"
output_dir.mkdir(exist_ok=True)

for location, entries in per_location.items():
    print(f"{location}:")
    for entry in entries:
        date, num_hours, more_or_less = entry
        if more_or_less == MoreOrLess.More:
            pass
            print(f"\t{date}: more than {num_hours} hours")
        elif more_or_less == MoreOrLess.Less:
            pass
            print(f"\t{date}: less than {num_hours} hours")
        else:
            raise NotImplementedError

    render_location_graph(location, entries, output_dir)

    print()
