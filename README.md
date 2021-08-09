# strava-weather-webhook

This cloud-hosted service creates a webhook to automatically update my new Strava activities with the AccuWeather RealFeel temperatures that occurred during the activity. This is circled in red in the screenshot below.

![](screenshot.jpg?raw=true "Strava weather webhook screenshot")

### Built with:
* [Strava API](https://developers.strava.com/)
* [AccuWeather API](https://developer.accuweather.com/)
* Asynchronous python design using Quart, Hypercorn, asyncio, aiohttp

**NOTE:** *The Strava post needs to occur within 24 hours of the start of the activity to get the hourly historical weather from AccuWeather.*
