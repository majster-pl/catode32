"""Playing behavior for energetic fun."""

from entities.behaviors.base import BaseBehavior


class PlayingBehavior(BaseBehavior):
    """Pet plays energetically.

    Phases:
    1. excited - Pet gets excited
    2. playing - Active play
    3. tired - Pet winds down
    """

    NAME = "playing"
    POSES = {
        "sitting.side.happy",
        "standing.side.happy",
        "sitting_silly.side.happy",
        "sitting.side.neutral",
    }

    # Trigger when playfulness is high
    TRIGGER_STAT = "playfulness"
    TRIGGER_THRESHOLD = 70
    TRIGGER_BELOW = False  # Trigger when ABOVE threshold
    PRIORITY = 30
    COOLDOWN = 60.0

    # Playing costs energy but satisfies playfulness
    STAT_EFFECTS = {"playfulness": -2.0, "energy": -0.5, "stimulation": 1.0}
    COMPLETION_BONUS = {"playfulness": -25, "fulfillment": 10}

    def __init__(self, character):
        """Initialize the playing behavior.

        Args:
            character: The CharacterEntity this behavior belongs to.
        """
        super().__init__(character)

        # Phase durations
        self.excited_duration = 1.0
        self.play_duration = 5.0
        self.tired_duration = 1.0

    def start(self, on_complete=None):
        """Begin playing.

        Args:
            on_complete: Optional callback when play finishes.
        """
        if self._active:
            return

        self._active = True
        self._phase = "excited"
        self._phase_timer = 0.0
        self._progress = 0.0
        self._pose_before = self._character.pose_name
        self._on_complete = on_complete

        self._character.set_pose("sitting.side.happy")

    def update(self, dt):
        """Update play phases.

        Args:
            dt: Delta time in seconds.
        """
        if not self._active:
            return

        self._phase_timer += dt

        if self._phase == "excited":
            if self._phase_timer >= self.excited_duration:
                self._phase = "playing"
                self._phase_timer = 0.0
                self._character.set_pose("sitting_silly.side.happy")

        elif self._phase == "playing":
            self._progress = min(1.0, self._phase_timer / self.play_duration)

            if self._phase_timer >= self.play_duration:
                self._phase = "tired"
                self._phase_timer = 0.0
                self._character.set_pose("sitting.side.neutral")

        elif self._phase == "tired":
            if self._phase_timer >= self.tired_duration:
                self.stop(completed=True)
