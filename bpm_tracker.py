class BPMTracker:
    def __init__(self):
        self.timestamps = []

    def add_timestamp(self, timestamp):
        self.timestamps.append(timestamp)
        # Keep only the last 5 timestamps
        if len(self.timestamps) > 10:
            self.timestamps.pop(0)

    def calculate_bpm(self):
        if len(self.timestamps) < 2:
            return 0  # Not enough data to calculate BPM

        # Calculate average difference between timestamps
        diffs = [self.timestamps[i] - self.timestamps[i - 1] for i in range(1, len(self.timestamps))]
        avg_diff = sum(diffs) / len(diffs)

        # Convert average difference to BPM (60 seconds per minute)
        if avg_diff == 0:
            return 0  # Prevent division by zero
        return 60 / avg_diff
