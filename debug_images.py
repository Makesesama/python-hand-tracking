#!/usr/bin/env python3
"""
Debug script to capture and save raw images from Ultraleap sensor.
This helps diagnose if the camera is working and oriented correctly.
"""

import sys
import time
import leap
import cv2
import numpy as np
from datetime import datetime


class ImageListener(leap.Listener):
    """Listener that captures and saves images from the Ultraleap sensor."""

    def __init__(self):
        super().__init__()
        self.image_count = 0
        self.max_images = 10
        self.save_interval = 1.0  # Save one image per second
        self.last_save_time = 0

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
        current_time = time.time()

        # Print hand count
        print(f"Frame {event.tracking_frame_id}: {len(event.hands)} hands detected")

        # Save images at intervals
        if (current_time - self.last_save_time >= self.save_interval and
            self.image_count < self.max_images):

            self.last_save_time = current_time

            # Try to get images from the event
            # Note: Images might not be available depending on service configuration
            if hasattr(event, 'images') and len(event.images) > 0:
                for i, image in enumerate(event.images):
                    self.save_image(image, i)
                    self.image_count += 1
            else:
                print("  No images available in tracking event (images might be disabled in service config)")

    def save_image(self, image, camera_id):
        """Save a leap image to disk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"leap_image_cam{camera_id}_{timestamp}.png"

        try:
            # Convert leap image to numpy array
            # Ultraleap images are typically grayscale
            width = image.properties.width
            height = image.properties.height

            # Get image data
            image_data = np.array(image.data, dtype=np.uint8)
            image_array = image_data.reshape((height, width))

            # Save image
            cv2.imwrite(filename, image_array)
            print(f"  Saved image: {filename} ({width}x{height})")

        except Exception as e:
            print(f"  Error saving image: {e}")


def main():
    print("Ultraleap Image Debug Tool")
    print("=" * 50)
    print("This will capture raw images from the sensor")
    print("Make sure 'allow_images: true' in /etc/ultraleap/hand_tracker_config.json")
    print("Press Ctrl+C to exit\n")

    # Create listener instance
    image_listener = ImageListener()

    # Create connection and add listener
    connection = leap.Connection()
    connection.add_listener(image_listener)

    # Start the connection
    with connection.open():
        # Set tracking mode to desktop
        connection.set_tracking_mode(leap.TrackingMode.Desktop)

        # Request images
        try:
            connection.set_policy(leap.PolicyFlag.Images)
            print("Requested images from service")
        except Exception as e:
            print(f"Warning: Could not request images: {e}")

        print("Tracking mode set to: Desktop")
        print("Waiting for frames...\n")

        try:
            # Keep running
            while image_listener.image_count < image_listener.max_images:
                time.sleep(0.1)

            print(f"\nCaptured {image_listener.image_count} images. Exiting.")

        except KeyboardInterrupt:
            print("\n\nStopping...")
            sys.exit(0)


if __name__ == "__main__":
    main()
