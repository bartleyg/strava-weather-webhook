import os


# https://developers.strava.com/
# https://developers.strava.com/docs/webhooks/
# https://developers.strava.com/docs/webhookexample/
# NOTE: To get the refresh token with proper scopes, go to
# https://developers.strava.com/playground/, open DevTools, and login with scopes
# activity:read_all,activity:write
# Replace new tab's incorrect browser url scope=activity%3Aread_all%20activity%3Awrite
# with scope=activity%3Aread_all%2cactivity%3Awrite and look at playground
# response to see the refresh_token to save.
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
strava_refresh_token = os.getenv("STRAVA_REFRESH_TOKEN")


async def get_access_token(session):
    # get a short-lived access token from the stored user (me) refresh token to
    # access any API calls
    global strava_refresh_token
    url = "https://www.strava.com/api/v3/oauth/token"
    url += f"?client_id={STRAVA_CLIENT_ID}"
    url += f"&client_secret={STRAVA_CLIENT_SECRET}"
    url += "&grant_type=refresh_token"
    url += f"&refresh_token={strava_refresh_token}"
    try:
        async with session.post(url) as r:
            if r.status >= 400:
                raise Exception(f"Error status: {r.status}: {await r.text()}.")
            data = await r.json()
    except Exception as e:
        print("strava.get_access_token: Exception:", e)
        return
    # store refresh token in global var in case it changed
    if data["refresh_token"] != strava_refresh_token:
        print(
            "Strava refresh token updated from "
            f"{strava_refresh_token} to {data['refresh_token']}."
        )
        strava_refresh_token = data["refresh_token"]
    return data.get("access_token")


async def get_activity(session, activity_id, access_token):
    # get the activity with id
    url = f"https://www.strava.com/api/v3/activities/{activity_id}"
    url += "?include_all_efforts=false"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        async with session.get(url, headers=headers) as r:
            if r.status >= 400:
                raise Exception(f"Error status: {r.status}: {await r.text()}.")
            data = await r.json()
    except Exception as e:
        print("strava.get_activity: Exception:", e)
        return
    return data


async def update_activity_description(session, activity_id, description, access_token):
    # update the description of activity with id
    url = f"https://www.strava.com/api/v3/activities/{activity_id}"
    payload = {"description": description}
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        async with session.put(url, json=payload, headers=headers) as r:
            if r.status >= 400:
                raise Exception(f"Error status: {r.status}: {await r.text()}.")
            data = await r.json()
    except Exception as e:
        print("strava.update_activity_description: Exception:", e)
        return
    return data
