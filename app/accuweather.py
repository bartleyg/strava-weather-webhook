import os


# https://developer.accuweather.com/apis
# NOTE: can't get historical temperatures or RealFeel further than last 24 hours
ACCUWEATHER_API_KEY = os.getenv("ACCUWEATHER_API_KEY")


async def get_location_key(session, latlong):
    # get key to access other API calls for latlong location
    url = "https://dataservice.accuweather.com/locations/v1/cities/geoposition/search"
    url += f"?apikey={ACCUWEATHER_API_KEY}&q={latlong}"
    try:
        async with session.get(url) as r:
            if r.status >= 400:
                raise Exception(f"Error status: {r.status}: {await r.text()}.")
            data = await r.json()
    except Exception as e:
        print("accuweather.get_location_key: Exception:", e)
        return
    return data.get("Key")


async def get_current_conditions(session, location_key):
    # returns array of 1 condition which can be 7 minutes old for example
    url = f"https://dataservice.accuweather.com/currentconditions/v1/{location_key}"
    url += f"?apikey={ACCUWEATHER_API_KEY}&details=true"
    try:
        async with session.get(url) as r:
            if r.status >= 400:
                raise Exception(f"Error status: {r.status}: {await r.text()}.")
            data = await r.json()
    except Exception as e:
        print("accuweather.get_current_conditions: Exception:", e)
        return
    return data


async def get_historical_conditions(session, location_key):
    # returns array of 24 hrs from -1 hr to -25 hrs from present
    url = f"https://dataservice.accuweather.com/currentconditions/v1/{location_key}"
    url += f"/historical/24"
    url += f"?apikey={ACCUWEATHER_API_KEY}&details=true"
    try:
        async with session.get(url) as r:
            if r.status >= 400:
                raise Exception(f"Error status: {r.status}: {await r.text()}.")
            data = await r.json()
    except Exception as e:
        print("accuweather.get_historical_conditions: Exception:", e)
        return
    return data
