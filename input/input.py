import leap
import msgspec
from msgspec_osc import MsgspecUDPClient
from typing import List
from collections import deque

class Vector3(msgspec.Struct, tag=False):
    x: float
    y: float
    z: float

class Quaternion(msgspec.Struct, tag=False):
    x: float
    y: float
    z: float
    w: float

class Bone(msgspec.Struct, tag=False):
    """Represents a single bone/phalange in a finger or the arm."""
    start_position: Vector3   # Position of the joint closer to the palm/wrist
    end_position: Vector3     # Position of the joint farther from the palm/wrist
    center: Vector3           # Center of the bone
    orientation: Quaternion   # Rotation of the bone
    length: float
    width: float

class Finger(msgspec.Struct, tag=False):
    """Represents a single finger (Thumb, Index, Middle, Ring, Pinky)."""
    id: int
    tip_position: Vector3
    is_extended: bool
    bones: List[Bone] # Typically 4 bones per finger (metacarpal, proximal, intermediate, distal)
    # An enum or string could be used for 'type' (thumb, index, etc.)

class Hand(msgspec.Struct, tag=False):
    """Represents the full tracking data for a single hand."""
    id: int
    is_left: bool
    confidence: float

    # Key metrics
    grab_strength: float # 0.0 to 1.0 (closed fist)
    pinch_strength: float # 0.0 to 1.0 (thumb/index pinch)
    pinch_distance: float # Distance between thumb and index tips

    # Positional data
    palm_position: Vector3
    palm_velocity: Vector3
    palm_normal: Vector3   # Normal vector pointing outward from the palm
    direction: Vector3     # Direction vector pointing from the palm toward the fingers
    
    # Arm/Wrist Data (often includes wrist and elbow positions)
    wrist_position: Vector3
    arm_elbow_position: Vector3
    
    # The fingers array
    fingers: List[Finger] # A list of 5 Finger structs

class TrackingEvent(msgspec.Struct, tag=False):
    """The root data structure for a single tracking frame."""
    tracking_frame_id: int
    timestamp: int # The raw tracking service timestamp (often in microseconds)
    hands: List[Hand] # A list of all detected Hand structs (0, 1, or 2)

class UltraleapListener(leap.Listener):
    """Listener that visualizes hand tracking data."""

    def __init__(self):
        super().__init__()
        self.client = MsgspecUDPClient("127.0.0.1", 5005)
        self.current_hands = []
        self.frame_id = 0
        self.fps_samples = deque(maxlen=30)
        self.last_time = None

    def on_connection_event(self, event):
        print("Connected to Ultraleap service")

    def on_device_event(self, event):
        try:
            with event.device.open():
                info = event.device.get_info()
        except leap.LeapCannotOpenDeviceError:
            info = event.device.get_info()
        print(f"Found device {info.serial}")

    def on_tracking_event(self, event):
        self.frame_id = event.tracking_frame_id
        self.current_hands = event.hands

        # Calculate FPS
        import time
        current_time = time.time()
        if self.last_time:
            fps = 1.0 / (current_time - self.last_time)
            self.fps_samples.append(fps)

            # Build the msgspec structs from the Leap Motion event data
            hands = []
            for hand in event.hands:
                # Convert fingers
                fingers = []
                for digit in hand.digits:
                    # Convert bones for this finger
                    bones = []
                    for bone in digit.bones:
                        bone_struct = Bone(
                            start_position=Vector3(x=bone.prev_joint.x, y=bone.prev_joint.y, z=bone.prev_joint.z),
                            end_position=Vector3(x=bone.next_joint.x, y=bone.next_joint.y, z=bone.next_joint.z),
                            center=Vector3(x=bone.center.x, y=bone.center.y, z=bone.center.z),
                            orientation=Quaternion(x=bone.rotation.x, y=bone.rotation.y, z=bone.rotation.z, w=bone.rotation.w),
                            length=bone.length,
                            width=bone.width
                        )
                        bones.append(bone_struct)

                    finger_struct = Finger(
                        id=digit.finger_id,
                        tip_position=Vector3(x=digit.tip_position.x, y=digit.tip_position.y, z=digit.tip_position.z),
                        is_extended=digit.is_extended,
                        bones=bones
                    )
                    fingers.append(finger_struct)

                # Get arm data
                arm = hand.arm

                hand_struct = Hand(
                    id=hand.id,
                    is_left=(hand.type == leap.HandType.Left),
                    confidence=hand.confidence,
                    grab_strength=hand.grab_strength,
                    pinch_strength=hand.pinch_strength,
                    pinch_distance=hand.pinch_distance,
                    palm_position=Vector3(x=hand.palm.position.x, y=hand.palm.position.y, z=hand.palm.position.z),
                    palm_velocity=Vector3(x=hand.palm.velocity.x, y=hand.palm.velocity.y, z=hand.palm.velocity.z),
                    palm_normal=Vector3(x=hand.palm.normal.x, y=hand.palm.normal.y, z=hand.palm.normal.z),
                    direction=Vector3(x=hand.palm.direction.x, y=hand.palm.direction.y, z=hand.palm.direction.z),
                    wrist_position=Vector3(x=arm.wrist.x, y=arm.wrist.y, z=arm.wrist.z),
                    arm_elbow_position=Vector3(x=arm.elbow.x, y=arm.elbow.y, z=arm.elbow.z),
                    fingers=fingers
                )
                hands.append(hand_struct)

            tracking_event = TrackingEvent(
                tracking_frame_id=event.tracking_frame_id,
                timestamp=event.timestamp,
                hands=hands
            )

            self.client.send_struct("/tracking/event", tracking_event)

        self.last_time = current_time

        
def main():
    # Create dispatcher
    listener = UltraleapListener()
    connection = leap.Connection()
    connection.add_listener(listener)

    with connection.open():
        try:
            pass
        except KeyboardInterrupt:
            print("\n\nStopping visualization...")
        finally:
            print("Done!")

if __name__ == "__main__":
    main()
