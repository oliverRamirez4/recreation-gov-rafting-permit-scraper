import argparse
import logging
import sys
from datetime import datetime

from enums.date_format import DateFormat


class RaftingArgumentParser(argparse.ArgumentParser):
    def __init__(self):
        super().__init__()
        self.add_argument(
            "--debug", "-d", action="store_true", help="Debug log level"
        )
        self.add_argument(
            "--start-date",
            required=True,
            help="Start date [YYYY-MM-DD]",
            type=self.TypeConverter.date,
        )
        self.add_argument(
            "--end-date",
            required=True,
            help="End date [YYYY-MM-DD]",
            type=self.TypeConverter.date,
        )
        self.add_argument(
            "--show-division-info",
            action="store_true",
            help="Display division/entry point details and availability dates.",
        )
        self.add_argument(
            "--min-permits",
            type=self.TypeConverter.positive_int,
            default=1,
            help=(
                "Minimum number of remaining permits to consider a date "
                "available (default: 1). Useful if your group needs multiple "
                "permits on the same launch date."
            ),
        )
        self.add_argument(
            "--json-output",
            action="store_true",
            help=(
                "Output JSON instead of human readable output. "
                "Includes precise information such as exact available dates, "
                "remaining permits, and which divisions have availability."
            ),
        )
        self.add_argument(
            "--weekends-only",
            action="store_true",
            help="Include only weekends (i.e. Friday or Saturday launch dates)",
        )
        permits_group = self.add_mutually_exclusive_group(required=True)
        permits_group.add_argument(
            "--permits",
            dest="permits",
            metavar="permit",
            nargs="+",
            help="Permit ID(s) from recreation.gov",
            type=int,
        )
        permits_group.add_argument(
            "--stdin",
            "-",
            action="store_true",
            help="Read list of permit ID(s) from stdin instead",
        )

    def parse_args(self, args=None, namespace=None):
        args = super().parse_args(args, namespace)
        args.permits = args.permits or [int(p.strip()) for p in sys.stdin]
        return args

    class TypeConverter:
        @classmethod
        def date(cls, date_str):
            try:
                return datetime.strptime(
                    date_str, DateFormat.INPUT_DATE_FORMAT.value
                )
            except ValueError as e:
                msg = "Not a valid date: '{0}'.".format(date_str)
                logging.critical(e)
                raise argparse.ArgumentTypeError(msg)

        @classmethod
        def positive_int(cls, i):
            i = int(i)
            if i <= 0:
                msg = "Not a valid positive integer: {0}".format(i)
                raise argparse.ArgumentTypeError(msg)
            return i
