# OSC Message Format Documentation

## Overview

This application sends hand tracking data via OSC using msgspec-serialized structs. The data is sent as MessagePack-encoded binary blobs over UDP.

## OSC Address

```
/tracking/event
```

## Data Format

The OSC message contains a single blob argument with msgspec (MessagePack) serialized data.

**OSC Message Structure:**
```
Address: /tracking/event
Arguments: [blob: msgspec-encoded TrackingEvent]
```

## Data Structure Hierarchy

### TrackingEvent (Root)
The top-level structure sent with each tracking frame.

```python
{
    "tracking_frame_id": int,      # Sequential frame identifier from Leap Motion
    "timestamp": int,               # Microsecond timestamp from tracking service
    "hands": [Hand, ...]           # Array of 0-2 detected hands
}
```

### Hand
Complete tracking data for a single detected hand.

```python
{
    "id": int,                      # Unique hand ID (persistent across frames)
    "is_left": bool,                # True if left hand, False if right hand
    "confidence": float,            # Tracking confidence (0.0 - 1.0)

    # Interaction Metrics
    "grab_strength": float,         # Closed fist strength (0.0 = open, 1.0 = closed)
    "pinch_strength": float,        # Thumb-index pinch strength (0.0 - 1.0)
    "pinch_distance": float,        # Distance between thumb and index fingertips (mm)

    # Palm Data
    "palm_position": Vector3,       # Palm center position (mm)
    "palm_velocity": Vector3,       # Palm velocity (mm/s)
    "palm_normal": Vector3,         # Vector perpendicular to palm (pointing out)
    "direction": Vector3,           # Vector from palm toward fingers

    # Arm Data
    "wrist_position": Vector3,      # Wrist joint position (mm)
    "arm_elbow_position": Vector3,  # Elbow joint position (mm)

    # Fingers
    "fingers": [Finger, ...]        # Array of 5 fingers
}
```

### Finger
Tracking data for a single finger (thumb, index, middle, ring, pinky).

```python
{
    "id": int,                      # Finger type ID (0=thumb, 1=index, 2=middle, 3=ring, 4=pinky)
    "tip_position": Vector3,        # Fingertip position (mm)
    "is_extended": bool,            # True if finger is extended/straight
    "bones": [Bone, ...]           # Array of 4 bones (metacarpal, proximal, intermediate, distal)
}
```

### Bone
Individual bone/phalanx data within a finger.

```python
{
    "start_position": Vector3,      # Joint position closer to palm/wrist (mm)
    "end_position": Vector3,        # Joint position farther from palm/wrist (mm)
    "center": Vector3,              # Center point of the bone (mm)
    "orientation": Quaternion,      # Bone rotation as quaternion
    "length": float,                # Bone length (mm)
    "width": float                  # Bone width/thickness (mm)
}
```

### Vector3
3D position or direction vector.

```python
{
    "x": float,
    "y": float,
    "z": float
}
```

### Quaternion
Rotation representation (x, y, z, w components).

```python
{
    "x": float,
    "y": float,
    "z": float,
    "w": float
}
```

## Example Data Structure

Here's what a complete tracking event with one hand might look like:

```python
{
    "tracking_frame_id": 12345,
    "timestamp": 1699564823456789,
    "hands": [
        {
            "id": 42,
            "is_left": True,
            "confidence": 0.98,
            "grab_strength": 0.15,
            "pinch_strength": 0.05,
            "pinch_distance": 45.3,
            "palm_position": {"x": 120.5, "y": 200.3, "z": -50.2},
            "palm_velocity": {"x": 5.2, "y": -2.1, "z": 1.3},
            "palm_normal": {"x": 0.1, "y": 0.98, "z": 0.15},
            "direction": {"x": 0.05, "y": 0.2, "z": -0.98},
            "wrist_position": {"x": 100.0, "y": 180.0, "z": -40.0},
            "arm_elbow_position": {"x": 50.0, "y": 100.0, "z": -20.0},
            "fingers": [
                {
                    "id": 0,  # Thumb
                    "tip_position": {"x": 150.2, "y": 210.5, "z": -60.1},
                    "is_extended": True,
                    "bones": [
                        {
                            "start_position": {"x": 110.0, "y": 190.0, "z": -45.0},
                            "end_position": {"x": 125.0, "y": 195.0, "z": -50.0},
                            "center": {"x": 117.5, "y": 192.5, "z": -47.5},
                            "orientation": {"x": 0.1, "y": 0.2, "z": 0.3, "w": 0.9},
                            "length": 32.5,
                            "width": 18.2
                        },
                        # ... 3 more bones
                    ]
                },
                # ... 4 more fingers
            ]
        }
    ]
}
```

## Receiving the Data

To receive this data, your OSC receiver needs to:

1. Listen on the configured port (default: 5005)
2. Handle OSC messages at address `/tracking/event`
3. Deserialize the blob argument using msgspec with the corresponding struct definitions

### Example Receiver (Python)

```python
import msgspec
from pythonosc import dispatcher, osc_server

# Define the same struct hierarchy as the sender
# (Vector3, Quaternion, Bone, Finger, Hand, TrackingEvent classes)

decoder = msgspec.msgpack.Decoder(TrackingEvent)

def handle_tracking_event(address, blob):
    tracking_event = decoder.decode(blob)
    print(f"Frame {tracking_event.tracking_frame_id}: {len(tracking_event.hands)} hands")
    for hand in tracking_event.hands:
        side = "Left" if hand.is_left else "Right"
        print(f"  {side} hand - Grab: {hand.grab_strength:.2f}, Pinch: {hand.pinch_strength:.2f}")

dispatcher = dispatcher.Dispatcher()
dispatcher.map("/tracking/event", handle_tracking_event)

server = osc_server.ThreadingOSCUDPServer(("127.0.0.1", 5005), dispatcher)
print("Serving on {}".format(server.server_address))
server.serve_forever()
```

## Coordinate System

Leap Motion uses a right-handed Cartesian coordinate system:

- **X-axis**: Positive values extend to the right
- **Y-axis**: Positive values extend upward
- **Z-axis**: Positive values extend toward the user (out of the device)
- **Units**: All positions are in millimeters (mm)
- **Velocities**: Millimeters per second (mm/s)

## Update Rate

The tracking data is sent at the Leap Motion's native frame rate:
- **Typical range**: 50-120 Hz depending on the device and tracking conditions
- **Frame ID**: Sequential identifier that increments with each frame
- **Timestamp**: Microsecond precision timestamp from the tracking service
