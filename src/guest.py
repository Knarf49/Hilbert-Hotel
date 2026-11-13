class Guest:
    @staticmethod
    def _validate_positive_int(value, name: str) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise ValueError(f"{name} must be a positive integer (>= 1)")

    def __init__(self, channel_id: int, sequence_id: int):
        self._validate_positive_int(channel_id, "Channel ID")
        self._validate_positive_int(sequence_id, "Sequence ID")
        self.channel_id = channel_id
        self.sequence_id = sequence_id
        self.room_no = self.compute_room_no(channel_id, sequence_id)

    @staticmethod
    def compute_room_no(c: int, s: int) -> int:
        Guest._validate_positive_int(c, "Channel ID")
        Guest._validate_positive_int(s, "Sequence ID")
        a = c - 1
        b = s - 1
        return ((a + b) * (a + b + 1)) // 2 + b + 1

    @property
    def guest_id(self) -> tuple[int, int]:
        return (self.channel_id, self.sequence_id)

    @property
    def guest_key(self) -> str:
        return f"guest:{self.channel_id}:{self.sequence_id}"
