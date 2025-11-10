#!/usr/bin/env python3
"""
Simple test to help position your hands correctly in the sensor's field of view.
Provides audio/visual feedback when hands are detected.
"""

import sys
import leap
import time


class SimpleFeedbackListener(leap.Listener):
    """Listener with clear feedback for hand detection."""

    def __init__(self):
        super().__init__()
        self.frame_count = 0
        self.hand_detected_count = 0
        self.last_hand_time = None

    def on_connection_event(self, event):
        print("✓ Connected to Ultraleap service")

    def on_device_event(self, event):
        try:
            with event.device.open():
                info = event.device.get_info()
        except leap.LeapCannotOpenDeviceError:
            info = event.device.get_info()
        print(f"✓ Found device: {info.serial}")

    def on_tracking_event(self, event):
        self.frame_count += 1

        if len(event.hands) > 0:
            self.hand_detected_count += 1
            self.last_hand_time = time.time()

            # Clear feedback
            print("\n" + "="*60)
            print(f"🎉 HAND DETECTED! Frame {event.tracking_frame_id}")
            print("="*60)

            for hand in event.hands:
                hand_type = "Left" if str(hand.type) == "HandType.Left" else "Right"
                palm = hand.palm

                print(f"\n{hand_type} Hand:")
                print(f"  Palm X: {palm.position.x:7.1f} mm")
                print(f"  Palm Y: {palm.position.y:7.1f} mm (height above sensor)")
                print(f"  Palm Z: {palm.position.z:7.1f} mm")
                print(f"  Confidence: {hand.confidence:.2f}")

                # Give feedback on positioning
                y = palm.position.y
                if y < 100:
                    print("  ⚠️  Too close! Move hand higher (100-400mm is best)")
                elif y > 400:
                    print("  ⚠️  Too far! Move hand closer (100-400mm is best)")
                else:
                    print("  ✓ Good height!")

        else:
            # Periodic status update
            if self.frame_count % 100 == 0:
                elapsed = time.time() - (self.last_hand_time or time.time())
                if self.hand_detected_count == 0:
                    print(f"Frame {event.tracking_frame_id:5d}: Still no hands detected. Keep trying...")
                else:
                    print(f"Frame {event.tracking_frame_id:5d}: No hands (last seen {elapsed:.1f}s ago)")


def main():
    print("\n" + "="*60)
    print("ULTRALEAP FIELD OF VIEW TEST")
    print("="*60)
    print("\nThis will help you find the correct hand position.\n")
    print("INSTRUCTIONS:")
    print("1. Place sensor flat on desk, USB cable away from you")
    print("2. Start with hand 20cm (8 inches) above the CENTER")
    print("3. Palm facing DOWN, fingers slightly spread")
    print("4. Move SLOWLY in a small circle")
    print("5. Try different heights: 15cm, 25cm, 35cm")
    print("\nField of view is a CONE extending upward from the device")
    print("If nothing detected after 30 seconds, sensor may be upside down\n")
    print("Press Ctrl+C to exit\n")

    time.sleep(2)

    listener = SimpleFeedbackListener()
    connection = leap.Connection()
    connection.add_listener(listener)

    with connection.open():
        connection.set_tracking_mode(leap.TrackingMode.Desktop)
        print("✓ Tracking started in Desktop mode")
        print("✓ Listening for tracking events\n")
        print("Waiting for hands...\n")

        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\n" + "="*60)
            print(f"SUMMARY:")
            print(f"  Total frames: {listener.frame_count}")
            print(f"  Hands detected in: {listener.hand_detected_count} frames")
            if listener.hand_detected_count > 0:
                print(f"  Success rate: {100*listener.hand_detected_count/listener.frame_count:.1f}%")
                print("\n✓ Sensor is working! Hands were detected.")
            else:
                print("\n✗ No hands detected. Check:")
                print("  - Camera orientation (flat, top side up?)")
                print("  - Hand position (directly above, 20cm high?)")
                print("  - Palm facing down?")
            print("="*60 + "\n")
            sys.exit(0)


if __name__ == "__main__":
    main()
