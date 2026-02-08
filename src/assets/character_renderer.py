from assets.poses import POSES


def get_point(sprite, key, frame=0):
    """Get a point value from a sprite, handling both static (int) and animated (list) values."""
    value = sprite[key]
    return value[frame] if isinstance(value, list) else value


class CharacterRenderer():
    def __init__(self, renderer):
        self.renderer = renderer

    def update_animation(self, context, dt):
        """Update and wrap animation counters based on current pose's frame counts."""
        pose_name = context.get("pose", "idle")
        pose = POSES[pose_name]

        body_frames = len(pose["body"]["frames"])
        head_frames = len(pose["head"]["frames"])
        tail_frames = len(pose["tail"]["frames"])

        context["blink"] = (context["blink"] + dt) % 10.0
        context["body"] = (context["body"] + dt) % body_frames
        context["head"] = (context["head"] + dt) % head_frames
        context["tail"] = (context["tail"] + dt * 4) % tail_frames

    def draw_character(self, context, x, y):
        pose_name = context.get("pose", "idle")
        pose = POSES[pose_name]

        # Body
        body = pose["body"]
        body_frame = int(context.get("body", 0)) % len(body["frames"])
        body_x = x - body["anchor_x"]
        body_y = y - body["anchor_y"]
        self.renderer.draw_sprite_obj(body, body_x, body_y, frame=body_frame)

        # Head
        head = pose["head"]
        head_frame = int(context.get("head", 0)) % len(head["frames"])
        head_root_x = body_x + get_point(body, "head_x", body_frame)
        head_root_y = body_y + get_point(body, "head_y", body_frame)

        head_x = head_root_x - head["anchor_x"]
        head_y = head_root_y - head["anchor_y"]
        self.renderer.draw_sprite_obj(head, head_x, head_y, frame=head_frame)

        # Eyes
        eyes = pose["eyes"]
        eye_frame = 0
        if context["blink"] < 0.9:
            eye_frame = 1 if (context["blink"] < 0.3 or context["blink"] > 0.6) else 2
        eye_x = head_x + get_point(head, "eye_x", head_frame) - eyes["anchor_x"]
        eye_y = head_y + get_point(head, "eye_y", head_frame) - eyes["anchor_y"]
        self.renderer.draw_sprite_obj(eyes, eye_x, eye_y, frame=eye_frame)

        # Tail
        tail = pose["tail"]
        tail_frame = int(context["tail"]) % len(tail["frames"])
        tail_root_x = body_x + get_point(body, "tail_x", body_frame)
        tail_root_y = body_y + get_point(body, "tail_y", body_frame)
        tail_x = tail_root_x - tail["anchor_x"]
        tail_y = tail_root_y - tail["anchor_y"]
        self.renderer.draw_sprite_obj(tail, tail_x, tail_y, frame=tail_frame)
