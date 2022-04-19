from quart import Quart, request, jsonify
import asyncio
import json

import process


# NOTE: Global variable per instance.
# An unfortunate workaround in Cloud Run with 1 instance to prevent duplicating
# an activity description update because Cloud Run can take ~10 seconds to run
# because of cold start, plus the processing is limited after the async response
# to the request, and the processing here is done afterwards.
# And strava will resend the event to the webhook if the update isn't
# acknowledged within a couple seconds. So we store the event and don't repeat
# when it's already seen.
events_seen = set()
app = Quart(__name__)

# webhook route that receives the event data
@app.post("/webhook")
async def post_webhook():
    event = await request.get_json()
    print("event received:")
    print(json.dumps(event, indent=4))

    # only process activity created events
    if not (event["object_type"] == "activity" and event["aspect_type"] == "create"):
        print("Event is not an activity created event.")
        return "OK", 200

    # don't process event if already seen
    activity_id = event["object_id"]
    if activity_id in events_seen:
        print(f"Event {activity_id} already seen.")
        return "OK", 200
    else:
        events_seen.add(activity_id)

    # return response while process event runs slowly async in background
    asyncio.create_task(process.process_event(event))
    return "OK", 200


# route used to verify the webhook for the subscription created
@app.get("/webhook")
async def verify_webhook():
    challenge = request.args.get("hub.challenge")
    if not challenge:
        return "GET /webhook missing 'hub.challenge' query", 403
    return jsonify({"hub.challenge": challenge})


@app.get("/")
async def index():
    return "OK", 200


if __name__ == "__main__":
    app.run("0.0.0.0", 80)
