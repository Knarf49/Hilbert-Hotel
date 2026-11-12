class Guest:
    def __init__(self, channel_id, sequence_id):
        if channel_id < 1 or sequence_id < 1:
            raise ValueError ("Channel and sequence ID must be positive integers (>= 1)")
        self.channel_id = channel_id
        self.sequence_id = sequence_id
        self.room_no = self.compute_room_no(channel_id, sequence_id)

    @staticmethod
    def compute_room_no(c, s):
        a = c-1
        b = s-1
        return((a+b)*(a+b+1)) // 2+b+1

    @property
    def guest_id(self):
        return(self.channel_id, self.sequence_id)
    @property
    def guest_key(self) :
        return f"guest:{self.channel_id}:{self.sequence_id}"