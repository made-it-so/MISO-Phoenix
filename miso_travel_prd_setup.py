"""
Registers the Sales Call Travel Automation goal and all component bounties
into the Goal Kernel and PRD Store.

Run once:
    python miso_travel_prd_setup.py

This creates:
  - 1 parent goal: "Sales Call Travel Automation"
  - 5 sub-goals + bounties (one per component)
  - 1 bounty for Consiglieri Live Call Support
"""
from miso_goal_kernel import create_goal, activate_goal
from miso_prd_store import create_bounty, print_board


def setup():
    print("[SETUP] Registering Sales Call Travel Automation in Goal Kernel...\n")

    # ── Parent goal ───────────────────────────────────────────────────────────
    parent = create_goal(
        title="Sales Call Travel Automation",
        description=(
            "Monitor sales calls for onsite meeting triggers. When detected, "
            "automatically book flights, hotel, and restaurant without human intervention. "
            "Consiglieri provides real-time decision support during the call."
        ),
        success_criteria=[
            "Travel trigger detected from transcript with >90% precision",
            "Round-trip flight booked within 60s of trigger confirmation",
            "Hotel booked within 1 mile of meeting address",
            "Restaurant reservation confirmed for evening prior to meeting",
            "Consiglieri live brief delivered within 5s of manual trigger",
        ],
        priority=2,
    )
    activate_goal(parent["id"])
    pid = parent["id"]
    print(f"\n  Parent goal: [{pid}]\n")

    # ── Sub-goals + bounties ──────────────────────────────────────────────────

    # 1. Transcript ingestor
    g1 = create_goal(
        title="Call Transcript Ingestor",
        description=(
            "Receive real-time or post-call transcripts from Zoom, Google Meet, "
            "or Teams via webhook. Also accept manual .vtt / .txt file drop."
        ),
        success_criteria=[
            "Zoom webhook endpoint receives transcript within 60s of call end",
            "Manual .vtt file drop processed correctly",
            "Transcript stored with metadata: participants, timestamp, duration",
        ],
        priority=2,
        parent_id=pid,
    )
    activate_goal(g1["id"])
    create_bounty(
        title="Call Transcript Ingestor",
        description=g1["description"],
        prd_blueprint={
            "architectureNodes": [
                {"id": 1, "type": "trigger",  "title": "Zoom Webhook",      "desc": "POST /webhook/zoom/transcript"},
                {"id": 2, "type": "trigger",  "title": "File Drop",         "desc": "Watch folder for .vtt/.txt"},
                {"id": 3, "type": "workflow", "title": "Transcript Parser", "desc": "Normalize to plain text + metadata"},
                {"id": 4, "type": "memory",   "title": "Call Archive",      "desc": "SQLite: call_id, participants, transcript, timestamp"},
            ],
            "mechanics": (
                "1. Register Zoom webhook at /webhook/zoom/transcript\n"
                "2. On POST: extract transcript JSON, normalize to plain text\n"
                "3. Also watch MISO_MONITOR_DIR for .vtt files (same normalization)\n"
                "4. Store in call_archive.db with metadata\n"
                "5. Emit event: TRANSCRIPT_READY(call_id) to trigger downstream agents"
            ),
            "dependencies": [
                {"id": "zoom_webhook_token", "name": "Zoom Webhook Verification Token", "status": "pending"},
            ],
        },
        goal_id=g1["id"],
        success_criteria=g1["success_criteria"],
    )

    # 2. Intent detector
    g2 = create_goal(
        title="Travel Trigger Intent Detector",
        description=(
            "Analyze transcript for onsite meeting signals. Extract structured "
            "data: city, date, duration, attendees. Fire TRAVEL_TRIGGER event."
        ),
        success_criteria=[
            "Detects explicit onsite language with >90% precision",
            "Extracts city and date with >85% accuracy",
            "False positive rate <5% on non-travel calls",
            "watch_for_triggers() runs on each 30s chunk automatically",
        ],
        priority=2,
        parent_id=pid,
    )
    activate_goal(g2["id"])
    create_bounty(
        title="Travel Trigger Intent Detector",
        description=g2["description"],
        prd_blueprint={
            "architectureNodes": [
                {"id": 1, "type": "agent",  "title": "Trigger Scanner",     "desc": "miso_consiglieri.watch_for_triggers() on each chunk"},
                {"id": 2, "type": "agent",  "title": "Structured Extractor","desc": "LLM extracts: city, date, duration, attendees"},
                {"id": 3, "type": "agent",  "title": "Confirmation Gate",   "desc": "If confidence < HIGH, prompt operator to confirm"},
            ],
            "mechanics": (
                "1. On TRANSCRIPT_READY: chunk transcript into 30s segments\n"
                "2. Run watch_for_triggers() on each chunk (regex-first, zero LLM cost)\n"
                "3. On travel pattern match: run structured LLM extraction\n"
                "4. If confidence HIGH: emit TRAVEL_TRIGGER(city, date, duration, attendees)\n"
                "5. If confidence MEDIUM: show operator confirmation UI before firing\n"
                "6. Log all detections to trigger_log.db"
            ),
        },
        goal_id=g2["id"],
        success_criteria=g2["success_criteria"],
    )

    # 3. Travel booker
    g3 = create_goal(
        title="Flight Booking Agent",
        description=(
            "On TRAVEL_TRIGGER: search and book the optimal round-trip flight "
            "using Amadeus or Duffel API. Apply stored traveler preferences."
        ),
        success_criteria=[
            "Amadeus/Duffel API integrated with live search",
            "Books preferred airline and seat class from preferences vault",
            "Confirms booking and emails itinerary within 60s of trigger",
            "Handles API credential failure with graceful fallback message",
        ],
        priority=3,
        parent_id=pid,
    )
    activate_goal(g3["id"])
    create_bounty(
        title="Flight Booking Agent",
        description=g3["description"],
        prd_blueprint={
            "architectureNodes": [
                {"id": 1, "type": "agent",  "title": "Flight Searcher", "desc": "Amadeus Flight Offers Search API"},
                {"id": 2, "type": "agent",  "title": "Flight Booker",   "desc": "Amadeus Flight Orders API"},
                {"id": 3, "type": "memory", "title": "Preferences Vault","desc": "Preferred airline, seat, FF number, home airport"},
            ],
            "mechanics": (
                "1. On TRAVEL_TRIGGER(city, date, duration):\n"
                "2. Load traveler prefs from preferences_vault.json\n"
                "3. Search Amadeus for round-trip flights: origin=home_airport, dest=city, date=date\n"
                "4. Filter by preferred airline, rank by price + layovers\n"
                "5. Book top result via Amadeus Flight Orders\n"
                "6. Store confirmation in bookings.db\n"
                "7. Emit FLIGHT_BOOKED(confirmation_number, itinerary)"
            ),
            "dependencies": [
                {"id": "amadeus_api_key", "name": "Amadeus API Key + Secret", "status": "pending"},
                {"id": "traveler_profile", "name": "Traveler passport/profile on file", "status": "pending"},
            ],
        },
        goal_id=g3["id"],
        success_criteria=g3["success_criteria"],
    )

    # 4. Hotel booker
    g4 = create_goal(
        title="Hotel Booking Agent",
        description=(
            "On TRAVEL_TRIGGER: search and book a hotel within 1 mile of the "
            "meeting address using Booking.com Affiliate or Expedia Rapid API."
        ),
        success_criteria=[
            "Hotel within 1 mile of meeting address",
            "Applies loyalty program numbers from preferences vault",
            "Books correct check-in/check-out dates relative to meeting",
            "Confirmation stored and emailed",
        ],
        priority=3,
        parent_id=pid,
    )
    activate_goal(g4["id"])
    create_bounty(
        title="Hotel Booking Agent",
        description=g4["description"],
        prd_blueprint={
            "architectureNodes": [
                {"id": 1, "type": "agent",  "title": "Hotel Searcher", "desc": "Expedia Rapid / Booking.com Affiliate API"},
                {"id": 2, "type": "agent",  "title": "Hotel Booker",   "desc": "Book selected property"},
                {"id": 3, "type": "memory", "title": "Preferences Vault","desc": "Preferred chains, loyalty numbers, room type"},
            ],
            "mechanics": (
                "1. On TRAVEL_TRIGGER(city, date, duration, meeting_address):\n"
                "2. Geocode meeting_address to lat/lon\n"
                "3. Search hotels within 1-mile radius for check-in=date-1, check-out=date+duration\n"
                "4. Filter by preferred chains, rank by proximity + rating\n"
                "5. Book via API, apply loyalty number\n"
                "6. Store in bookings.db, emit HOTEL_BOOKED"
            ),
            "dependencies": [
                {"id": "hotel_api_key", "name": "Expedia Rapid API or Booking.com Affiliate key", "status": "pending"},
                {"id": "geocoding_key",  "name": "Google Maps Geocoding API key", "status": "pending"},
            ],
        },
        goal_id=g4["id"],
        success_criteria=g4["success_criteria"],
    )

    # 5. Restaurant reserver
    g5 = create_goal(
        title="Restaurant Reservation Agent",
        description=(
            "Book a dinner reservation at a top restaurant near the meeting "
            "location for the evening before the meeting, using Resy or OpenTable API."
        ),
        success_criteria=[
            "Reservation at a restaurant with 4.5+ stars within 1 mile of hotel",
            "Booked for the evening prior to meeting date",
            "Party size matches attendee count from trigger",
            "Confirmation stored and included in itinerary email",
        ],
        priority=3,
        parent_id=pid,
    )
    activate_goal(g5["id"])
    create_bounty(
        title="Restaurant Reservation Agent",
        description=g5["description"],
        prd_blueprint={
            "architectureNodes": [
                {"id": 1, "type": "agent",  "title": "Restaurant Finder",  "desc": "Yelp Fusion / Google Places for top restaurants"},
                {"id": 2, "type": "agent",  "title": "Reservation Booker", "desc": "Resy API or OpenTable Connect"},
                {"id": 3, "type": "agent",  "title": "Fallback Notifier",  "desc": "If API unavailable, output top 3 with phone numbers"},
            ],
            "mechanics": (
                "1. On HOTEL_BOOKED(hotel_address, date, party_size):\n"
                "2. Search Yelp/Google Places: restaurants within 0.5mi, rating>=4.5, cuisine!=fast_food\n"
                "3. Rank by rating + Michelin/James Beard recognition\n"
                "4. Attempt Resy booking for top result, evening of date-1, party_size\n"
                "5. If Resy fails: try OpenTable Connect\n"
                "6. If both fail: output top 3 with phone numbers for manual booking\n"
                "7. Emit RESTAURANT_BOOKED or RESTAURANT_MANUAL_ACTION_REQUIRED"
            ),
            "dependencies": [
                {"id": "resy_api",       "name": "Resy API access (requires Resy partnership)", "status": "pending"},
                {"id": "opentable_api",  "name": "OpenTable Connect API", "status": "pending"},
                {"id": "yelp_api",       "name": "Yelp Fusion API key (free tier available)", "status": "pending"},
            ],
        },
        goal_id=g5["id"],
        success_criteria=g5["success_criteria"],
    )

    # 6. Consiglieri live call support bounty (code already exists, this tracks integration)
    create_bounty(
        title="Consiglieri Live Call Support — Zoom Integration",
        description=(
            "Wire miso_consiglieri.live_counsel() and watch_for_triggers() into "
            "the Zoom transcript pipeline so counsel fires automatically on trigger "
            "detection and is available on manual hotkey during the call."
        ),
        prd_blueprint={
            "architectureNodes": [
                {"id": 1, "type": "agent",   "title": "Trigger Scanner",      "desc": "watch_for_triggers() on each 30s chunk"},
                {"id": 2, "type": "agent",   "title": "Live Counsel Endpoint","desc": "POST /counsel/live with transcript + question"},
                {"id": 3, "type": "trigger", "title": "Manual Hotkey",        "desc": "Global hotkey fires live_counsel() on demand"},
                {"id": 4, "type": "trigger", "title": "Auto-fire",            "desc": "Auto-fires when travel/buying/objection trigger detected"},
            ],
            "mechanics": (
                "1. On each TRANSCRIPT_CHUNK: run watch_for_triggers()\n"
                "2. If trigger detected: auto-call live_counsel(transcript_so_far)\n"
                "   and display brief in overlay/notification\n"
                "3. Manual: global hotkey (e.g., Ctrl+Shift+M) → live_counsel()\n"
                "4. Frontier escalation: use Claude/GPT-4o for <5s latency\n"
                "5. Display brief as desktop overlay — non-blocking, dismissable"
            ),
        },
        goal_id=pid,
        success_criteria=[
            "live_counsel() responds within 5s using frontier model",
            "watch_for_triggers() runs on each chunk with zero LLM cost",
            "Manual hotkey fires from anywhere on desktop",
            "Travel trigger auto-fires booking pipeline without additional input",
        ],
    )

    print("\n" + "=" * 60)
    print("SETUP COMPLETE")
    print_board()


if __name__ == "__main__":
    setup()
