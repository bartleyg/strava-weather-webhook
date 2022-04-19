import asyncio
import aiohttp
import json
import time
import dateutil.parser
from datetime import datetime, timedelta

import strava
import accuweather


# webhook business logic to process an event/activity
async def process_event(event):
    start = time.time()
    async with aiohttp.ClientSession() as sesh:
        # get a strava access_token and get strava activity details
        activity_id = event["object_id"]
        access_token = await strava.get_access_token(sesh)
        if not access_token:
            return
        activity = await strava.get_activity(sesh, activity_id, access_token)
        print("activity:")
        print(activity)
        if not activity:
            return

        # use strava activity start lat/long to get accuweather location key
        latlong = f'{activity["start_latlng"][0]}, {activity["start_latlng"][1]}'
        location_key = await accuweather.get_location_key(sesh, latlong)
        if not location_key:
            return

        # concurrently get location's current and hourly historical conditions
        current_cond, historical_conds = await asyncio.gather(
            accuweather.get_current_conditions(sesh, location_key),
            accuweather.get_historical_conditions(sesh, location_key),
        )
        if (not current_cond) or (not historical_conds):
            return
        historical_conds = current_cond + historical_conds

        # get activity's weather conditions
        activity_conds = get_conditions_during_activity(activity, historical_conds)
        if len(activity_conds) == 0:
            weather_desc = (
                "No weather conditions found. Was the Strava upload"
                + " within 24 hours of start of activity?"
            )
        else:
            weather_desc = make_weather_description(activity_conds)

        print("weather_desc:", weather_desc)
        # prepend new weather description to original activity description
        act_desc = f'\n{activity["description"]}' if activity["description"] else ""
        description = weather_desc + act_desc

        # update the strava activity with the new description
        await strava.update_activity_description(
            sesh, activity_id, description, access_token
        )
        seconds = time.time() - start
        print(f"process_event took {seconds:.3f}s.")


def get_conditions_during_activity(activity, historical_conds):
    # return only the weather conditions during or closest to activity time
    TIME_TOLERANCE = timedelta(minutes=15)
    # start_date_local: "2021-07-28T18:46:00Z"
    start = dateutil.parser.parse(activity["start_date_local"], ignoretz=True)
    end = start + timedelta(seconds=activity["elapsed_time"])
    print("start-15m:", start - TIME_TOLERANCE, "end+15m:", end + TIME_TOLERANCE)

    conditions = []
    timedeltas_from_activity = []
    # save the conditions within the activity window
    for cond in historical_conds:
        # LocalObservationDateTime: "2021-07-31T08:58:00-05:00"
        observe_time = dateutil.parser.parse(
            cond["LocalObservationDateTime"], ignoretz=True
        )
        if start - TIME_TOLERANCE <= observe_time <= end + TIME_TOLERANCE:
            print("weather observe_time in activity window:", observe_time)
            conditions.append(cond)
        # store the timedelta from activity
        observe_timedelta = min(abs(start - observe_time), abs(end - observe_time))
        timedeltas_from_activity.append(observe_timedelta)

    # save the closest condition if a short activity
    # where no condition is within the activity window.
    # exclude condition where activity could be too far in past (3 hrs).
    if len(conditions) == 0:
        print("no weather conditions found within activity window.")
        min_timedelta = min(timedeltas_from_activity)
        print("min_timedelta:", min_timedelta)
        if min_timedelta <= timedelta(hours=3):
            print("activity within 3 hrs of a weather condition.")
            conditions.append(
                historical_conds[timedeltas_from_activity.index(min_timedelta)]
            )
        else:
            print("activity too old, not within 3 hrs of a weather condition.")

    return conditions


def make_weather_description(conditions):
    # make the strava description from the activity's weather conditions
    realfeels_sun = []
    realfeels_shade = []
    for cond in conditions:
        realfeels_sun.append(cond["RealFeelTemperature"]["Imperial"]["Value"])
        realfeels_shade.append(cond["RealFeelTemperatureShade"]["Imperial"]["Value"])
    print("realfeels_sun:", realfeels_sun, "realfeels_shade:", realfeels_shade)

    rf_sun_lo = int(min(realfeels_sun))
    rf_sun_hi = int(max(realfeels_sun))
    rf_shade_lo = int(min(realfeels_shade))
    rf_shade_hi = int(max(realfeels_shade))

    # description can be single measurement or a range
    if rf_sun_lo == rf_sun_hi:
        rf_sun_desc = f"{rf_sun_hi}\u00b0F"
    else:
        rf_sun_desc = f"{rf_sun_lo}-{rf_sun_hi}\u00b0F"
    if rf_shade_lo == rf_shade_hi:
        rf_shade_desc = f"{rf_shade_hi}\u00b0F"
    else:
        rf_shade_desc = f"{rf_shade_lo}-{rf_shade_hi}\u00b0F"

    description = f"{rf_sun_desc} RealFeel. {rf_shade_desc} RealFeel Shade."
    return description
