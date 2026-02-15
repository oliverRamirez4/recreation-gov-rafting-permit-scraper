# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import json
import logging
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from itertools import count, groupby

from dateutil import rrule

from clients.recreation_client import RecreationClient
from enums.date_format import DateFormat
from enums.emoji import Emoji
from utils import formatter
from utils.rafting_argparser import RaftingArgumentParser

LOG = logging.getLogger(__name__)
log_formatter = logging.Formatter(
    "%(asctime)s - %(process)s - %(levelname)s - %(message)s"
)
sh = logging.StreamHandler()
sh.setFormatter(log_formatter)
LOG.addHandler(sh)


def get_permit_information(permit_id, start_date, end_date):
    """
    Fetches permit availability from recreation.gov for the given permit ID
    and date range.

    The permit availability API returns data structured by "divisions"
    (entry points / river sections). Each division has date_availability
    with total and remaining permit counts per day.

    The output of this function looks like this:

    {
        "<division_id>": {
            "name": "<division_name>",
            "available_dates": [
                {"date": "<ISO date>", "remaining": N, "total": N},
                ...
            ]
        }
    }
    """

    # Get each first of the month for months in the range we care about.
    start_of_month = datetime(start_date.year, start_date.month, 1)
    months = list(
        rrule.rrule(rrule.MONTHLY, dtstart=start_of_month, until=end_date)
    )

    # Get data for each month.
    api_data = []
    for month_date in months:
        resp = RecreationClient.get_permit_availability(permit_id, month_date)

        api_data.append(resp)

    # Get permit info to resolve division names.
    permit_info = RecreationClient.get_permit_info(permit_id)
    divisions_info = permit_info.get("payload", {}).get("divisions", {})

    # Collapse the data into the described output format.
    data = {}

    for month_data in api_data:
        payload = month_data.get("payload", month_data)
        availability = payload.get("availability", {})


        for division_id, division_data in availability.items():
            if division_id not in data:
                div_info = divisions_info.get(str(division_id), {})
                data[division_id] = {
                    "name": div_info.get("name", "Division {}".format(division_id)),
                    "available_dates": [],
                }

            date_availability = division_data.get("date_availability", {})
            for date_str, avail_info in date_availability.items():
                remaining = avail_info.get("remaining", 0)
                total = avail_info.get("total", 0)

                if remaining <= 0:
                    continue

                # Parse date and filter to requested range.
                date_obj = datetime.strptime(
                    date_str, DateFormat.ISO_DATE_FORMAT_RESPONSE.value
                )
                if date_obj < start_date or date_obj >= end_date:
                    continue

                data[division_id]["available_dates"].append(
                    {
                        "date": date_str,
                        "remaining": remaining,
                        "total": total,
                    }
                )

    # Sort available dates for each division.
    for division_id in data:
        data[division_id]["available_dates"].sort(key=lambda x: x["date"])

    return data


def is_weekend(date):
    weekday = date.weekday()
    return weekday == 4 or weekday == 5


def get_num_available_dates(
    permit_information, start_date, end_date, weekends_only=False, min_permits=1
):
    """
    Given permit information, count the number of divisions that have
    available dates in the requested range, and organize results.
    """
    num_days = (end_date - start_date).days
    dates_in_range = [end_date - timedelta(days=i) for i in range(1, num_days + 1)]
    if weekends_only:
        dates_in_range = list(filter(is_weekend, dates_in_range))
    dates_in_range_set = set(
        formatter.format_date(
            i, format_string=DateFormat.ISO_DATE_FORMAT_RESPONSE.value
        )
        for i in dates_in_range
    )

    available_divisions = {}
    total_divisions = len(permit_information)

    for division_id, division_data in permit_information.items():
        division_name = division_data["name"]
        matching_dates = []

        for avail in division_data["available_dates"]:
            if avail["date"] in dates_in_range_set and avail["remaining"] >= min_permits:
                matching_dates.append(avail)

        if matching_dates:
            available_divisions[division_id] = {
                "name": division_name,
                "dates": matching_dates,
            }

    return len(available_divisions), total_divisions, available_divisions


def check_permit(permit_id, start_date, end_date, weekends_only=False, min_permits=1):
    permit_information = get_permit_information(permit_id, start_date, end_date)
    LOG.debug(
        "Information for permit {}: {}".format(
            permit_id, json.dumps(permit_information, indent=2)
        )
    )

    permit_info = RecreationClient.get_permit_info(permit_id)
    permit_name = permit_info.get("payload", {}).get("name", "Permit {}".format(permit_id))

    current, maximum, available_divisions = get_num_available_dates(
        permit_information, start_date, end_date,
        weekends_only=weekends_only, min_permits=min_permits,
    )
    return current, maximum, available_divisions, permit_name


def generate_human_output(
    info_by_permit_id, start_date, end_date,
):
    out = []
    has_availabilities = False
    for permit_id, info in info_by_permit_id.items():
        current, maximum, available_divisions, permit_name = info
        if current:
            emoji = Emoji.RAFTING_SUCCESS.value
            has_availabilities = True
        else:
            emoji = Emoji.RAFTING_FAILURE.value

        out.append(
            "{emoji} {permit_name} ({permit_id}): {current} division(s) with availability out of {maximum} division(s)".format(
                emoji=emoji,
                permit_name=permit_name,
                permit_id=permit_id,
                current=current,
                maximum=maximum,
            )
        )

        # Always show available dates. Show division headers when >1 division.
        if available_divisions:
            show_division_headers = len(available_divisions) > 1 or maximum > 1
            for division_id, div_data in available_divisions.items():
                if show_division_headers:
                    out.append(
                        "  * {name} (Division {div_id}):".format(
                            name=div_data["name"], div_id=division_id
                        )
                    )
                for date_info in div_data["dates"]:
                    date_nice = formatter.format_date(
                        datetime.strptime(
                            date_info["date"],
                            DateFormat.ISO_DATE_FORMAT_RESPONSE.value,
                        ),
                        format_string=DateFormat.INPUT_DATE_FORMAT.value,
                    )
                    out.append(
                        "  {indent}* {date}: {remaining}/{total} permits remaining".format(
                            indent="  " if show_division_headers else "",
                            date=date_nice,
                            remaining=date_info["remaining"],
                            total=date_info["total"],
                        )
                    )

    if has_availabilities:
        out.insert(
            0,
            "there are permits available from {start} to {end}!!!".format(
                start=start_date.strftime(DateFormat.INPUT_DATE_FORMAT.value),
                end=end_date.strftime(DateFormat.INPUT_DATE_FORMAT.value),
            ),
        )
    else:
        out.insert(0, "There are no permits available :(")
    return "\n".join(out), has_availabilities


def generate_json_output(info_by_permit_id):
    availabilities_by_permit_id = {}
    has_availabilities = False
    for permit_id, info in info_by_permit_id.items():
        current, _, available_divisions, _ = info
        if current:
            has_availabilities = True
            availabilities_by_permit_id[permit_id] = available_divisions

    return json.dumps(availabilities_by_permit_id), has_availabilities


def main(permits, json_output=False):
    info_by_permit_id = {}
    for permit_id in permits:
        info_by_permit_id[permit_id] = check_permit(
            permit_id,
            args.start_date,
            args.end_date,
            weekends_only=args.weekends_only,
            min_permits=args.min_permits,
        )

    if json_output:
        output, has_availabilities = generate_json_output(info_by_permit_id)
    else:
        output, has_availabilities = generate_human_output(
            info_by_permit_id,
            args.start_date,
            args.end_date,
        )
    print(output)
    return has_availabilities


if __name__ == "__main__":
    parser = RaftingArgumentParser()
    args = parser.parse_args()

    if args.debug:
        LOG.setLevel(logging.DEBUG)

    main(args.permits, json_output=args.json_output)
