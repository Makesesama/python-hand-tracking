#!/usr/bin/env python3
"""
Simple program to get hand and finger coordinates from Ultraleap sensor.
Requires the Ultraleap Gemini service to be running.
Uses the official leapc-python-bindings.
"""

import sys
import leap


class TrackingListener(leap.Listener):
    """Listener that receives tracking events from the Ultraleap service."""

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
        print(f"\nFrame {event.tracking_frame_id} with {len(event.hands)} hands")

        for hand in event.hands:
            hand_type = "Left" if str(hand.type) == "HandType.Left" else "Right"

            print(f"\n  {hand_type} Hand (ID: {hand.id}):")

            # Palm position
            palm = hand.palm
            print(f"    Palm position: x={palm.position.x:.2f}, y={palm.position.y:.2f}, z={palm.position.z:.2f} mm")
            print(f"    Palm normal: x={palm.normal.x:.2f}, y={palm.normal.y:.2f}, z={palm.normal.z:.2f}")
            print(f"    Palm velocity: x={palm.velocity.x:.2f}, y={palm.velocity.y:.2f}, z={palm.velocity.z:.2f} mm/s")
            print(f"    Palm width: {palm.width:.2f} mm")

            # Digits (thumb and fingers)
            digit_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]

            for i, digit in enumerate(hand.digits):
                digit_name = digit_names[i] if i < len(digit_names) else f"Digit {i}"

                # Each digit has bones: metacarpal, proximal, intermediate, distal
                if digit.distal:
                    tip_pos = digit.distal.next_joint
                    print(f"    {digit_name} tip: x={tip_pos.x:.2f}, y={tip_pos.y:.2f}, z={tip_pos.z:.2f} mm")

            # Arm information
            if hand.arm:
                arm = hand.arm
                print(f"    Arm direction: x={arm.direction.x:.2f}, y={arm.direction.y:.2f}, z={arm.direction.z:.2f}")
                print(f"    Elbow position: x={arm.prev_joint.x:.2f}, y={arm.prev_joint.y:.2f}, z={arm.prev_joint.z:.2f} mm")
                print(f"    Wrist position: x={arm.next_joint.x:.2f}, y={arm.next_joint.y:.2f}, z={arm.next_joint.z:.2f} mm")

            # Hand metrics
            print(f"    Grab strength: {hand.grab_strength:.2f}")
            print(f"    Pinch strength: {hand.pinch_strength:.2f}")
            print(f"    Pinch distance: {hand.pinch_distance:.2f} mm")


def main():
    print("Starting Ultraleap hand tracking...")
    print("Make sure the Ultraleap Gemini service is running!")
    print("Press Ctrl+C to exit\n")

    # Create listener instance
    tracking_listener = TrackingListener()

    # Create connection and add listener
    connection = leap.Connection()
    connection.add_listener(tracking_listener)

    # Start the connection
    with connection.open():
        # Set tracking mode to desktop (try ScreenTop if this doesn't work)
        connection.set_tracking_mode(leap.TrackingMode.Desktop)
        print(f"Tracking mode set to: Desktop")

        try:
            # Keep running until interrupted
            while True:
                pass
        except KeyboardInterrupt:
            print("\n\nStopping tracking...")
            sys.exit(0)


if __name__ == "__main__":
    main()
