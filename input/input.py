import leap
from msgspec_osc import MsgspecUDPClient
from collections import deque
from tracking_structs import leap_event_to_msgspec

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

            # Convert Leap Motion event to msgspec structs and send
            tracking_event = leap_event_to_msgspec(event)
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
