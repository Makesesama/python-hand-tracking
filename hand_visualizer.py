#!/usr/bin/env python3
"""
Real-time visualization of Ultraleap hand tracking data.
Shows hands and fingers in 3D space with OpenCV.
"""

import sys
import leap
import cv2
import numpy as np
from collections import deque


class VisualizationListener(leap.Listener):
    """Listener that visualizes hand tracking data."""

    def __init__(self):
        super().__init__()
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
        self.last_time = current_time


def world_to_screen(x, y, z, width, height, scale=1.5):
    """
    Convert 3D world coordinates (mm) to 2D screen coordinates.
    Ultraleap coordinates: X (left-right), Y (up-down), Z (far-near)
    """
    # Scale and translate
    screen_x = int(width / 2 + x * scale)
    screen_y = int(height / 2 - y * scale)  # Flip Y for screen coordinates

    return screen_x, screen_y


def draw_hand(img, hand, width, height, scale=1.5):
    """Draw a hand with palm and finger positions."""

    # Determine hand color
    if str(hand.type) == "HandType.Left":
        hand_color = (255, 100, 100)  # Blue for left
        hand_name = "Left"
    else:
        hand_color = (100, 100, 255)  # Red for right
        hand_name = "Right"

    # Draw palm
    palm = hand.palm
    palm_x, palm_y = world_to_screen(palm.position.x, palm.position.y, palm.position.z, width, height, scale)

    # Palm circle (size based on distance)
    palm_size = max(5, int(20 - palm.position.z / 50))
    cv2.circle(img, (palm_x, palm_y), palm_size, hand_color, -1)
    cv2.circle(img, (palm_x, palm_y), palm_size + 2, (255, 255, 255), 2)

    # Draw palm label
    cv2.putText(img, hand_name, (palm_x + 15, palm_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, hand_color, 2)

    # Draw fingers
    finger_names = ["Thumb", "Index", "Middle", "Ring", "Pinky"]
    finger_colors = [
        (255, 200, 100),  # Thumb - cyan
        (100, 255, 100),  # Index - green
        (100, 255, 255),  # Middle - yellow
        (255, 100, 255),  # Ring - magenta
        (200, 100, 255),  # Pinky - purple
    ]

    for i, digit in enumerate(hand.digits):
        if i >= len(finger_names):
            continue

        color = finger_colors[i]

        # Draw each bone in the finger
        bones = [digit.metacarpal, digit.proximal, digit.intermediate, digit.distal]
        points = []

        for bone in bones:
            if bone:
                prev_x, prev_y = world_to_screen(bone.prev_joint.x, bone.prev_joint.y,
                                                 bone.prev_joint.z, width, height, scale)
                next_x, next_y = world_to_screen(bone.next_joint.x, bone.next_joint.y,
                                                 bone.next_joint.z, width, height, scale)
                points.extend([(prev_x, prev_y), (next_x, next_y)])

        # Draw lines connecting finger joints
        for j in range(0, len(points) - 1, 2):
            if j + 1 < len(points):
                cv2.line(img, points[j], points[j + 1], color, 2)

        # Draw finger tip
        if digit.distal:
            tip = digit.distal.next_joint
            tip_x, tip_y = world_to_screen(tip.x, tip.y, tip.z, width, height, scale)
            cv2.circle(img, (tip_x, tip_y), 5, color, -1)
            cv2.circle(img, (tip_x, tip_y), 7, (255, 255, 255), 1)

        # Draw joint circles
        for point in points[::2]:  # Every other point (joints)
            cv2.circle(img, point, 3, (255, 255, 255), -1)

    # Draw arm if available
    if hand.arm:
        arm = hand.arm
        elbow_x, elbow_y = world_to_screen(arm.prev_joint.x, arm.prev_joint.y,
                                           arm.prev_joint.z, width, height, scale)
        wrist_x, wrist_y = world_to_screen(arm.next_joint.x, arm.next_joint.y,
                                           arm.next_joint.z, width, height, scale)

        # Draw arm line
        cv2.line(img, (elbow_x, elbow_y), (wrist_x, wrist_y), hand_color, 3)
        cv2.circle(img, (elbow_x, elbow_y), 6, hand_color, -1)
        cv2.circle(img, (wrist_x, wrist_y), 6, hand_color, -1)

    return img


def draw_info_panel(img, listener, width, height):
    """Draw information panel with stats."""

    # Background for info panel
    cv2.rectangle(img, (10, 10), (width - 10, 120), (0, 0, 0), -1)
    cv2.rectangle(img, (10, 10), (width - 10, 120), (255, 255, 255), 2)

    # Frame info
    cv2.putText(img, f"Frame: {listener.frame_id}", (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # FPS
    if listener.fps_samples:
        avg_fps = sum(listener.fps_samples) / len(listener.fps_samples)
        cv2.putText(img, f"FPS: {avg_fps:.1f}", (20, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    # Hand count
    hand_count = len(listener.current_hands)
    hand_text = f"Hands: {hand_count}"
    color = (100, 255, 100) if hand_count > 0 else (100, 100, 255)
    cv2.putText(img, hand_text, (20, 85),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # Instructions
    cv2.putText(img, "Press 'q' to quit", (20, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    # Hand details
    if hand_count > 0:
        y_offset = 140
        for hand in listener.current_hands:
            hand_type = "Left" if str(hand.type) == "HandType.Left" else "Right"
            palm = hand.palm

            info_text = f"{hand_type}: Y={palm.position.y:.0f}mm Grab={hand.grab_strength:.2f}"
            cv2.putText(img, info_text, (20, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            y_offset += 25

    return img


def draw_coordinate_grid(img, width, height):
    """Draw reference grid and axes."""

    # Center lines
    center_x, center_y = width // 2, height // 2
    cv2.line(img, (center_x, 0), (center_x, height), (50, 50, 50), 1)
    cv2.line(img, (0, center_y), (width, center_y), (50, 50, 50), 1)

    # Grid lines every 100 pixels
    for i in range(0, width, 100):
        cv2.line(img, (i, 0), (i, height), (30, 30, 30), 1)
    for i in range(0, height, 100):
        cv2.line(img, (0, i), (width, i), (30, 30, 30), 1)

    # Axis labels
    cv2.putText(img, "X+", (width - 40, center_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)
    cv2.putText(img, "Y+", (center_x + 10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)

    return img


def main():
    print("Ultraleap Hand Tracking Visualizer")
    print("=" * 50)
    print("Starting visualization...")
    print("Press 'q' to quit\n")

    # Create window
    window_name = "Ultraleap Hand Tracking"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 1200, 800)

    # Create listener
    listener = VisualizationListener()
    connection = leap.Connection()
    connection.add_listener(listener)

    with connection.open():
        connection.set_tracking_mode(leap.TrackingMode.Desktop)
        print("Tracking started!\n")

        try:
            while True:
                # Create blank image
                width, height = 1200, 800
                img = np.zeros((height, width, 3), dtype=np.uint8)

                # Draw grid
                img = draw_coordinate_grid(img, width, height)

                # Draw hands
                for hand in listener.current_hands:
                    img = draw_hand(img, hand, width, height, scale=1.5)

                # Draw info panel
                img = draw_info_panel(img, listener, width, height)

                # Show image
                cv2.imshow(window_name, img)

                # Check for quit
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' or ESC
                    break

        except KeyboardInterrupt:
            print("\n\nStopping visualization...")

        finally:
            cv2.destroyAllWindows()
            print("Done!")


if __name__ == "__main__":
    main()
