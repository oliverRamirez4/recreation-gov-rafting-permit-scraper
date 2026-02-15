# Rafting Permit Availability Scraper

This script scrapes https://recreation.gov for **rafting permit** availability. It checks permit divisions (entry points / river sections) and reports which dates still have remaining permits.

**Note:** Please don't abuse this script. Most folks out there don't know how to run scrapers against websites, so you're at an unfair advantage by using this.

## Example Usage

```
$ python rafting.py --start-date 2026-06-01 --end-date 2026-06-30 --permits 233393
🚣 Desolation Gray - Green River Permit (233393): 1 division(s) with availability out of 1 division(s)
```

You can also read from stdin. Define a file (e.g. `permits.txt`) with permit IDs:
```
233393
```
and then use it like this:
```
$ python rafting.py --start-date 2026-06-01 --end-date 2026-06-30 --stdin < permits.txt
```

### Detailed Division Info

To see which divisions/entry points have availability and how many permits remain, use `--show-division-info`:
```
$ python rafting.py --start-date 2026-06-01 --end-date 2026-06-30 --permits 233393 --show-division-info
there are permits available from 2026-06-01 to 2026-06-30!!!
🚣 Desolation Gray - Green River Permit (233393): 1 division(s) with availability out of 1 division(s)
  * Desolation-Gray Canyons of the Green River (Division 282):
    * 2026-06-01: 1/6 permits remaining
```

### Minimum Permits

If your group needs multiple permits on the same launch date, use `--min-permits`:
```
$ python rafting.py --start-date 2026-06-01 --end-date 2026-06-30 --permits 233393 --min-permits 3
```

### Weekends Only

To filter results to only Friday/Saturday launch dates:
```
$ python rafting.py --start-date 2026-06-01 --end-date 2026-06-30 --permits 233393 --weekends-only
```

### JSON Output

To get machine-readable JSON output:
```
$ python rafting.py --start-date 2026-06-01 --end-date 2026-06-30 --permits 233393 --json-output
```

## Getting Permit IDs

Go to https://recreation.gov and search for the rafting permit or river you want. Click on it in the search results. The URL will look like `https://www.recreation.gov/permits/<number>`. That number is the permit ID.

For example, the Desolation-Gray Canyons of the Green River permit is at:
`https://www.recreation.gov/permits/233393`

So the permit ID is `233393`.

## CLI Options

| Argument | Description |
|---|---|
| `--permits` | Permit ID(s) from recreation.gov (required, or use `--stdin`) |
| `--start-date` | Start date in YYYY-MM-DD format (required) |
| `--end-date` | End date in YYYY-MM-DD format (required) |
| `--show-division-info` | Show detailed division/entry point availability |
| `--min-permits` | Minimum remaining permits to consider a date available (default: 1) |
| `--json-output` | Output JSON instead of human-readable text |
| `--weekends-only` | Only show Friday/Saturday launch dates |
| `--debug` / `-d` | Enable debug logging |

## Installation

Python 3.9+ is recommended.
```
python3 -m venv myvenv
source myvenv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
# You're good to go!
```

## Running Tests

All tests should pass before a pull request gets merged. To run all the tests, cd into the project directory and run:
```bash
python -m unittest
```

## Development

This code is formatted using black and isort:
```
black -l 80 --py36 *.py
isort *.py
```
Note: `black` only really supports 3.6+ so watch out!

---

## Campsite Availability Scraping

This project also includes a **campsite availability** scraper, forked from [banool/recreation-gov-campsite-checker](https://github.com/banool/recreation-gov-campsite-checker).

### Example Usage (Camping)
```
$ python camping.py --start-date 2018-07-20 --end-date 2018-07-23 --parks 232448 232450 232447 232770
❌ TUOLUMNE MEADOWS: 0 site(s) available out of 148 site(s)
🏕 LOWER PINES: 11 site(s) available out of 73 site(s)
❌ UPPER PINES: 0 site(s) available out of 235 site(s)
❌ BASIN MONTANA CAMPGROUND: 0 site(s) available out of 30 site(s)
```

You can also read from stdin. Define a file (e.g. `parks.txt`) with park IDs:
```
232447
232449
232450
232448
```
```
$ python camping.py --start-date 2018-07-20 --end-date 2018-07-23 --stdin < parks.txt
```

### Show Campsite Info

Pass `--show-campsite-info` along with `--nights <int>` to see which campsites are available:
```
$ python camping.py --start-date 2018-07-20 --end-date 2018-07-23 --parks 232448 232450 232447 232770 --show-campsite-info --nights 1
```

### Number of Nights

Search for a specific number of contiguous nights within a date range using `--nights`:
```
$ python camping.py --start-date 2020-06-01 --end-date 2020-06-30 --nights 5 234038
```

### Getting Park IDs

Go to https://recreation.gov and search for the campground you want. The URL will look like `https://www.recreation.gov/camping/campgrounds/<number>`. That number is the park ID.

### Getting Campsite IDs

Search for a campground and then select a specific campsite. The URL will look like `https://www.recreation.gov/camping/campsites/<number>`. That number is the campsite ID. Use it with `--campsite-ids`.

### Excluding Specific Campsites

Define a file (e.g. `excluded.txt`) with one campsite ID per line and use `--exclusion-file`:
```
$ python camping.py --start-date 2018-07-20 --end-date 2018-07-23 --parks 232448 --exclusion-file excluded.txt
```

## Twitter Notification

If you want to be notified about availabilities via Twitter:
1. Make an app at https://developer.twitter.com/en/apps.
2. Update the values in `twitter_credentials.json` to match your keys.
3. Pipe the output into `notifier.py`:

```
python camping.py --start-date 2018-07-20 --end-date 2018-07-23 --parks 70926 70928 | python notifier.py @your_handle
```

## Credits

Originally based on https://github.com/bri-bri/yosemite-camping. Campsite checker forked from [banool/recreation-gov-campsite-checker](https://github.com/banool/recreation-gov-campsite-checker).
