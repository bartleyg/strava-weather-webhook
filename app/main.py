from quart import Quart, request, jsonify
import asyncio
import json

import process


app = Quart(__name__)

# webhook route that receives the event data
@app.post("/webhook")
async def post_webhook():
    event = await request.get_json()
    print("event received:")
    print(json.dumps(event, indent=4))
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
