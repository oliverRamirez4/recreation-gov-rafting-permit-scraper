import unittest

import rafting
from enums.date_format import DateFormat
from enums.emoji import Emoji
from utils.rafting_argparser import RaftingArgumentParser


class TestRafting(unittest.TestCase):
    def testGetNumAvailableDates_AggregatesDataForMultipleDivisions(self):
        permit_info = {
            "100": {
                "name": "Empty Division",
                "available_dates": [],
            },
            "200": {
                "name": "Some River Section",
                "available_dates": [
                    {"date": "2022-06-22T00:00:00Z", "remaining": 3, "total": 6},
                    {"date": "2022-06-23T00:00:00Z", "remaining": 1, "total": 6},
                ],
            },
            "300": {
                "name": "Another River Section",
                "available_dates": [
                    {"date": "2022-06-22T00:00:00Z", "remaining": 5, "total": 10},
                    {"date": "2022-06-25T00:00:00Z", "remaining": 2, "total": 10},
                ],
            },
        }

        current, maximum, available_divisions = rafting.get_num_available_dates(
            permit_info,
            RaftingArgumentParser.TypeConverter.date("2022-06-22"),
            RaftingArgumentParser.TypeConverter.date("2022-06-24"),
        )

        self.assertEqual(current, 2)
        self.assertEqual(maximum, 3)
        self.assertNotIn("100", available_divisions)
        self.assertIn("200", available_divisions)
        self.assertIn("300", available_divisions)

    def testGetNumAvailableDates_WeekendsOnly(self):
        permit_info = {
            "200": {
                "name": "Some River Section",
                "available_dates": [
                    # Wednesday
                    {"date": "2022-06-22T00:00:00Z", "remaining": 3, "total": 6},
                    # Friday
                    {"date": "2022-06-24T00:00:00Z", "remaining": 1, "total": 6},
                ],
            },
        }

        current, maximum, available_divisions = rafting.get_num_available_dates(
            permit_info,
            RaftingArgumentParser.TypeConverter.date("2022-06-20"),
            RaftingArgumentParser.TypeConverter.date("2022-06-26"),
            weekends_only=True,
        )

        self.assertEqual(current, 1)
        # Only the Friday date should show up
        self.assertIn("200", available_divisions)
        dates = [d["date"] for d in available_divisions["200"]["dates"]]
        self.assertIn("2022-06-24T00:00:00Z", dates)
        self.assertNotIn("2022-06-22T00:00:00Z", dates)

    def testGenerateOutputToHuman_DefaultOutputWithAvailabilities(self):
        """Single division permit: no division headers shown."""
        start_date = RaftingArgumentParser.TypeConverter.date("2022-06-01")
        end_date = RaftingArgumentParser.TypeConverter.date("2022-07-01")
        permit_name = "Some River Permit"
        permit_id = 233393
        current = 1
        maximum = 1

        expected = "\n".join(
            [
                "there are permits available from {start} to {end}!!!",
                "{emoji} {permit_name} ({permit_id}): {current} division(s) with availability out of {maximum} division(s)",
                "  * 2022-06-22: 3/6 permits remaining",
            ]
        ).format(
            start=start_date.strftime(DateFormat.INPUT_DATE_FORMAT.value),
            end=end_date.strftime(DateFormat.INPUT_DATE_FORMAT.value),
            emoji=Emoji.RAFTING_SUCCESS.value,
            permit_name=permit_name,
            permit_id=permit_id,
            current=current,
            maximum=maximum,
        )

        info_by_permit_id = {
            permit_id: (
                current,
                maximum,
                {
                    "282": {
                        "name": "Desolation-Gray Canyons",
                        "dates": [
                            {"date": "2022-06-22T00:00:00Z", "remaining": 3, "total": 6},
                        ],
                    }
                },
                permit_name,
            )
        }
        output, has_avail = rafting.generate_human_output(
            info_by_permit_id, start_date, end_date
        )
        self.assertEqual(output, expected)
        self.assertTrue(has_avail)

    def testGenerateOutputToHuman_DefaultOutputWithNoAvailabilities(self):
        start_date = RaftingArgumentParser.TypeConverter.date("2022-06-01")
        end_date = RaftingArgumentParser.TypeConverter.date("2022-07-01")
        permit_name = "Some River Permit"
        permit_id = 233393
        current = 0
        maximum = 2

        expected = "\n".join(
            [
                "There are no permits available :(",
                "{emoji} {permit_name} ({permit_id}): {current} division(s) with availability out of {maximum} division(s)",
            ]
        ).format(
            emoji=Emoji.RAFTING_FAILURE.value,
            permit_name=permit_name,
            permit_id=permit_id,
            current=current,
            maximum=maximum,
        )

        info_by_permit_id = {permit_id: (current, maximum, {}, permit_name)}
        output, has_avail = rafting.generate_human_output(
            info_by_permit_id, start_date, end_date
        )
        self.assertEqual(output, expected)
        self.assertFalse(has_avail)

    def testGenerateOutputToHuman_MultiDivisionShowsHeaders(self):
        """When >1 division exists, division name headers are auto-shown."""
        start_date = RaftingArgumentParser.TypeConverter.date("2022-06-01")
        end_date = RaftingArgumentParser.TypeConverter.date("2022-07-01")
        permit_name = "Some River Permit"
        permit_id = 233393
        current = 2
        maximum = 2

        expected = "\n".join(
            [
                "there are permits available from {start} to {end}!!!",
                "{emoji} {permit_name} ({permit_id}): {current} division(s) with availability out of {maximum} division(s)",
                "  * Section A (Division 100):",
                "    * 2022-06-22: 3/6 permits remaining",
                "  * Section B (Division 200):",
                "    * 2022-06-25: 2/8 permits remaining",
            ]
        ).format(
            start=start_date.strftime(DateFormat.INPUT_DATE_FORMAT.value),
            end=end_date.strftime(DateFormat.INPUT_DATE_FORMAT.value),
            emoji=Emoji.RAFTING_SUCCESS.value,
            permit_name=permit_name,
            permit_id=permit_id,
            current=current,
            maximum=maximum,
        )

        info_by_permit_id = {
            permit_id: (
                current,
                maximum,
                {
                    "100": {
                        "name": "Section A",
                        "dates": [
                            {"date": "2022-06-22T00:00:00Z", "remaining": 3, "total": 6},
                        ],
                    },
                    "200": {
                        "name": "Section B",
                        "dates": [
                            {"date": "2022-06-25T00:00:00Z", "remaining": 2, "total": 8},
                        ],
                    },
                },
                permit_name,
            )
        }
        output, has_avail = rafting.generate_human_output(
            info_by_permit_id, start_date, end_date,
        )
        self.assertEqual(output, expected)
        self.assertTrue(has_avail)

    def testGetNumAvailableDates_MinPermitsFilter(self):
        """--min-permits filters out dates with fewer remaining permits."""
        permit_info = {
            "200": {
                "name": "Some River Section",
                "available_dates": [
                    {"date": "2022-06-22T00:00:00Z", "remaining": 1, "total": 6},
                    {"date": "2022-06-23T00:00:00Z", "remaining": 3, "total": 6},
                ],
            },
        }

        # With min_permits=2, the date with remaining=1 should be excluded
        current, maximum, available_divisions = rafting.get_num_available_dates(
            permit_info,
            RaftingArgumentParser.TypeConverter.date("2022-06-22"),
            RaftingArgumentParser.TypeConverter.date("2022-06-24"),
            min_permits=2,
        )

        self.assertEqual(current, 1)
        dates = [d["date"] for d in available_divisions["200"]["dates"]]
        self.assertNotIn("2022-06-22T00:00:00Z", dates)
        self.assertIn("2022-06-23T00:00:00Z", dates)

    def testGetNumAvailableDates_MinPermitsExcludesEntireDivision(self):
        """If no dates in a division meet min_permits, that division is excluded."""
        permit_info = {
            "200": {
                "name": "Some River Section",
                "available_dates": [
                    {"date": "2022-06-22T00:00:00Z", "remaining": 1, "total": 6},
                ],
            },
        }

        current, maximum, available_divisions = rafting.get_num_available_dates(
            permit_info,
            RaftingArgumentParser.TypeConverter.date("2022-06-22"),
            RaftingArgumentParser.TypeConverter.date("2022-06-24"),
            min_permits=2,
        )

        self.assertEqual(current, 0)
        self.assertNotIn("200", available_divisions)

    def testGenerateJsonOutput_WithAvailabilities(self):
        permit_id = 233393
        available_divisions = {
            "282": {
                "name": "Desolation-Gray Canyons",
                "dates": [
                    {"date": "2022-06-22T00:00:00Z", "remaining": 3, "total": 6},
                ],
            }
        }
        info_by_permit_id = {
            permit_id: (1, 1, available_divisions, "Some Permit")
        }

        output, has_avail = rafting.generate_json_output(info_by_permit_id)
        self.assertTrue(has_avail)
        import json
        parsed = json.loads(output)
        self.assertIn(str(permit_id), parsed)

    def testGenerateJsonOutput_WithNoAvailabilities(self):
        permit_id = 233393
        info_by_permit_id = {
            permit_id: (0, 1, {}, "Some Permit")
        }

        output, has_avail = rafting.generate_json_output(info_by_permit_id)
        self.assertFalse(has_avail)


class TestRaftingArgParser(unittest.TestCase):
    def setUp(self):
        self.start_date = ["--start-date", "2022-01-01"]
        self.end_date = ["--end-date", "2022-01-02"]
        self.permits = ["--permits", "233393"]
        self.default_args = []
        self.default_args.extend(self.start_date)
        self.default_args.extend(self.end_date)
        self.default_args.extend(self.permits)

    def testAcceptsMultiplePermitIds(self):
        args = ["--permits", "233393", "234567"]
        args.extend(self.start_date)
        args.extend(self.end_date)
        parsed = RaftingArgumentParser().parse_args(args)
        self.assertEqual(parsed.permits, [233393, 234567])

    def testAcceptsBasicArgs(self):
        parsed = RaftingArgumentParser().parse_args(self.default_args)
        self.assertEqual(parsed.permits, [233393])
        self.assertFalse(parsed.weekends_only)
        self.assertFalse(parsed.json_output)

    def testAcceptsWeekendsOnly(self):
        args = self.default_args + ["--weekends-only"]
        parsed = RaftingArgumentParser().parse_args(args)
        self.assertTrue(parsed.weekends_only)

    def testAcceptsJsonOutput(self):
        args = self.default_args + ["--json-output"]
        parsed = RaftingArgumentParser().parse_args(args)
        self.assertTrue(parsed.json_output)

    def testAcceptsMinPermits(self):
        args = self.default_args + ["--min-permits", "3"]
        parsed = RaftingArgumentParser().parse_args(args)
        self.assertEqual(parsed.min_permits, 3)

    def testDefaultMinPermitsIsOne(self):
        parsed = RaftingArgumentParser().parse_args(self.default_args)
        self.assertEqual(parsed.min_permits, 1)


if __name__ == "__main__":
    unittest.main()
