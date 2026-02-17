# Action definitions and handlers for pet interactions

from assets.effects import (
    SPEECH_BUBBLE,
    BUBBLE_HEART,
    BUBBLE_QUESTION,
    BUBBLE_EXCLAIM,
    BUBBLE_NOTE,
    BUBBLE_STAR,
)

# Map bubble names to sprites
BUBBLE_SPRITES = {
    "heart": BUBBLE_HEART,
    "question": BUBBLE_QUESTION,
    "exclaim": BUBBLE_EXCLAIM,
    "note": BUBBLE_NOTE,
    "star": BUBBLE_STAR,
}

# Action definitions
# Each action specifies stat changes and reaction (pose, bubble, duration)
ACTIONS = {
    "kiss": {
        "stats": {"affection": 10},
        "reaction": {
            "pose": "sitting.forward.happy",
            "bubble": "heart",
            "duration": 2.5,
        },
    },
    "pets": {
        "stats": {"affection": 5},
        "reaction": {
            "pose": "sitting.forward.content",
            "bubble": "note",
            "duration": 2.0,
        },
    },
    "psst": {
        "stats": {"curiosity": 3},
        "reaction": {
            "pose": "sitting.forward.aloof",
            "bubble": "question",
            "duration": 1.5,
        },
    },
    "snack": {
        "stats": {"fullness": 10},
        "reaction": {
            "pose": "sitting.forward.happy",
            "bubble": "heart",
            "duration": 2.0,
        },
    },
    "toy": {
        "stats": {"playfulness": 15, "stimulation": 10},
        "reaction": {
            "pose": "sitting.forward.happy",
            "bubble": "exclaim",
            "duration": 2.0,
        },
    },
    # Outside-specific actions
    "point_bird": {
        "stats": {"curiosity": 10, "stimulation": 5},
        "reaction": {
            "pose": "sitting.side.aloof",
            "bubble": "exclaim",
            "duration": 2.0,
        },
    },
    "throw_stick": {
        "stats": {"playfulness": 15, "energy": -10},
        "reaction": {
            "pose": "sitting.side.happy",
            "bubble": "star",
            "duration": 2.5,
        },
    },
    "treat": {
        "stats": {"fullness": 5, "affection": 3},
        "reaction": {
            "pose": "sitting.side.happy",
            "bubble": "heart",
            "duration": 2.0,
        },
    },
}


def apply_action(action_key, context, character, reaction_manager):
    """Apply an action's stat changes and trigger its reaction.

    Args:
        action_key: Key into ACTIONS dict (e.g., "kiss", "pets")
        context: GameContext to modify stats on
        character: CharacterEntity to set pose on
        reaction_manager: ReactionManager to trigger reaction on

    Returns:
        True if action was found and applied, False otherwise
    """
    action = ACTIONS.get(action_key)
    if not action:
        return False

    # Apply stat changes
    for stat, delta in action.get("stats", {}).items():
        current = getattr(context, stat, 0)
        new_value = current + delta
        # Clamp to 0-100
        new_value = max(0, min(100, new_value))
        setattr(context, stat, new_value)

    # Trigger reaction
    reaction = action.get("reaction")
    if reaction_manager and reaction:
        reaction_manager.trigger_from_config(reaction, character)

    return True


class ReactionManager:
    """Manages reaction animations for pet interactions."""

    def __init__(self):
        self.timer = 0
        self.duration = 0
        self.bubble = None

    @property
    def active(self):
        """Return True if a reaction is currently playing."""
        return self.bubble is not None

    def trigger_from_config(self, reaction_config, character):
        """Trigger a reaction from a config dict.

        Args:
            reaction_config: Dict with pose, bubble, duration keys
            character: CharacterEntity to set pose on
        """
        character.set_pose(reaction_config["pose"])
        self.bubble = reaction_config["bubble"]
        self.duration = reaction_config["duration"]
        self.timer = reaction_config["duration"]

    def update(self, dt, character, default_pose):
        """Update reaction timer and revert pose when done.

        Args:
            dt: Delta time in seconds
            character: CharacterEntity to revert pose on
            default_pose: Pose name to revert to when reaction ends
        """
        if self.timer > 0:
            self.timer -= dt
            if self.timer <= 0:
                character.set_pose(default_pose)
                self.bubble = None

    def draw(self, renderer, char_screen_x, char_y, mirror=False):
        """Draw the reaction bubble if active.

        Args:
            renderer: Renderer to draw with
            char_screen_x: Character's x position on screen (after camera offset)
            char_y: Character's y position
            mirror: If True, position bubble on right side and mirror bubble sprite
        """
        if not self.bubble:
            return

        # Calculate animation progress (0 at start, 1 at end)
        progress = 0
        if self.duration > 0:
            progress = 1 - (self.timer / self.duration)

        # Position bubble relative to character's head
        # Drift upward as progress increases
        drift_amount = 10
        bubble_y = int(char_y) - 45 - int(progress * drift_amount)

        if mirror:
            # Position bubble to the right of the character
            bubble_x = char_screen_x + 15
        else:
            # Position bubble to the left of the character
            bubble_x = char_screen_x - SPEECH_BUBBLE["width"] - 15

        # Draw bubble frame (mirrored if needed so tail points correct direction)
        renderer.draw_sprite_obj(SPEECH_BUBBLE, bubble_x, bubble_y, mirror_h=mirror)

        # Draw content sprite centered inside bubble (inverted)
        content_sprite = BUBBLE_SPRITES.get(self.bubble)
        if content_sprite:
            content_x = bubble_x + 4
            content_y = bubble_y + 2
            renderer.draw_sprite_obj(
                content_sprite, content_x, content_y,
                invert=True, transparent=True, transparent_color=1
            )
