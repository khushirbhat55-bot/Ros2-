#!/usr/bin/env python3
"""
Robot Delivery Server
FastAPI backend that bridges the web interface to ROS2 navigation goals.
Run with: python3 robot_server.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import subprocess
import threading
import time

app = FastAPI(title="Robot Delivery Server")

# Allow frontend to talk to this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Shop coordinates in the Gazebo world (x, y) ──────────────────────────────
SHOPS = {
    "kirana":      {"name": "Kirana Store",     "x":  5.0, "y":  6.0, "color": "#f97316"},
    "medical":     {"name": "Medical Store",    "x": -5.0, "y":  6.0, "color": "#3b82f6"},
    "chai":        {"name": "Chai Stall",       "x":  5.0, "y": -6.0, "color": "#ef4444"},
    "stationery":  {"name": "Stationery Store", "x": -5.0, "y": -6.0, "color": "#a855f7"},
}

# Current robot status
robot_status = {
    "state": "idle",       # idle | navigating | arrived | error
    "message": "Robot is ready",
    "pickup": None,
    "delivery": None,
}

class DeliveryRequest(BaseModel):
    pickup: str
    delivery: str

def send_nav_goal(shop_id: str, label: str):
    """Send a navigation goal to ROS2 using ros2 action CLI."""
    shop = SHOPS[shop_id]
    x, y = shop["x"], shop["y"]

    cmd = [
        "ros2", "action", "send_goal",
        "/navigate_to_pose",
        "nav2_msgs/action/NavigateToPose",
        f"""{{
            "pose": {{
                "header": {{"frame_id": "map"}},
                "pose": {{
                    "position": {{"x": {x}, "y": {y}, "z": 0.0}},
                    "orientation": {{"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}}
                }}
            }}
        }}"""
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0
    except Exception as e:
        print(f"Navigation error: {e}")
        return False

def run_delivery(pickup_id: str, delivery_id: str):
    """Run the full delivery sequence in a background thread."""
    global robot_status

    # Step 1: Go to pickup
    robot_status["state"] = "navigating"
    robot_status["message"] = f"🚗 Going to {SHOPS[pickup_id]['name']} for pickup..."
    print(robot_status["message"])

    success = send_nav_goal(pickup_id, "pickup")

    if not success:
        robot_status["state"] = "error"
        robot_status["message"] = "❌ Failed to reach pickup location"
        return

    # Step 2: Arrived at pickup
    robot_status["message"] = f"📦 Picked up from {SHOPS[pickup_id]['name']}! Going to {SHOPS[delivery_id]['name']}..."
    print(robot_status["message"])
    time.sleep(2)

    # Step 3: Go to delivery
    success = send_nav_goal(delivery_id, "delivery")

    if not success:
        robot_status["state"] = "error"
        robot_status["message"] = "❌ Failed to reach delivery location"
        return

    # Step 4: Done!
    robot_status["state"] = "arrived"
    robot_status["message"] = f"✅ Delivered to {SHOPS[delivery_id]['name']} successfully!"
    print(robot_status["message"])
    time.sleep(3)
    robot_status["state"] = "idle"
    robot_status["message"] = "Robot is ready"

# ── API Routes ────────────────────────────────────────────────────────────────

@app.get("/shops")
def get_shops():
    return SHOPS

@app.get("/status")
def get_status():
    return robot_status

@app.post("/deliver")
def start_delivery(req: DeliveryRequest):
    global robot_status

    if robot_status["state"] == "navigating":
        return {"success": False, "message": "Robot is already on a mission!"}

    if req.pickup == req.delivery:
        return {"success": False, "message": "Pickup and delivery cannot be the same shop!"}

    if req.pickup not in SHOPS or req.delivery not in SHOPS:
        return {"success": False, "message": "Invalid shop selected!"}

    robot_status["pickup"] = req.pickup
    robot_status["delivery"] = req.delivery

    # Run delivery in background thread so API responds immediately
    thread = threading.Thread(target=run_delivery, args=(req.pickup, req.delivery))
    thread.daemon = True
    thread.start()

    return {
        "success": True,
        "message": f"Mission started! Picking up from {SHOPS[req.pickup]['name']} → delivering to {SHOPS[req.delivery]['name']}"
    }

@app.post("/cancel")
def cancel_mission():
    global robot_status
    # Stop the robot
    subprocess.run(["ros2", "topic", "pub", "--once", "/cmd_vel",
                   "geometry_msgs/msg/Twist", "{}"], capture_output=True)
    robot_status["state"] = "idle"
    robot_status["message"] = "Mission cancelled. Robot is ready."
    return {"success": True, "message": "Mission cancelled"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Robot Delivery Server starting...")
    print("📡 Open http://localhost:8000 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8000)
