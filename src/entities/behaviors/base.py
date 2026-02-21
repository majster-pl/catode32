"""Base class for all character behaviors."""


class BaseBehavior:
    """Abstract base class for all behaviors.

    Provides common interface and stat-affecting infrastructure.
    Subclasses should override NAME and implement their own
    update() and draw() logic with phases.
    """

    # Override in subclasses
    NAME = "base"

    # Triggering configuration (override in subclasses)
    TRIGGER_STAT = None  # e.g., "energy"
    TRIGGER_THRESHOLD = 50  # Behavior eligible when stat crosses threshold
    TRIGGER_BELOW = True  # True = eligible when below, False = when above
    PRIORITY = 50  # Lower = higher priority (0-100)
    COOLDOWN = 60.0  # Seconds between automatic triggers

    # Stat effects (override in subclasses)
    STAT_EFFECTS = {}  # e.g., {"energy": 0.5} = +0.5/sec during behavior
    COMPLETION_BONUS = {}  # e.g., {"energy": 10} = +10 on complete

    def __init__(self, character):
        """Initialize the behavior.

        Args:
            character: The CharacterEntity this behavior belongs to.
        """
        self._character = character

        # State
        self._active = False
        self._phase = None
        self._phase_timer = 0.0
        self._pose_before = None
        self._on_complete = None
        self._progress = 0.0  # 0.0 to 1.0

        # Cooldown tracking
        self._last_trigger_time = -self.COOLDOWN  # Allow immediate first trigger

    @property
    def active(self):
        """Return True if this behavior is currently active."""
        return self._active

    @property
    def progress(self):
        """Return the behavior's progress from 0.0 to 1.0."""
        return self._progress

    @property
    def phase(self):
        """Return the current phase name."""
        return self._phase

    def can_trigger(self, context, current_time):
        """Check if this behavior can be triggered automatically.

        Args:
            context: The GameContext to check stats from.
            current_time: Current elapsed game time in seconds.

        Returns:
            True if this behavior is eligible to trigger.
        """
        # Check cooldown
        if current_time - self._last_trigger_time < self.COOLDOWN:
            return False

        # Check stat threshold
        if self.TRIGGER_STAT:
            stat_value = getattr(context, self.TRIGGER_STAT, 50)
            if self.TRIGGER_BELOW:
                return stat_value < self.TRIGGER_THRESHOLD
            else:
                return stat_value > self.TRIGGER_THRESHOLD

        return False

    def start(self, on_complete=None):
        """Begin the behavior.

        Args:
            on_complete: Optional callback function called when behavior finishes.
                         Receives (completed: bool, progress: float).
        """
        if self._active:
            return

        self._active = True
        self._phase = "start"
        self._phase_timer = 0.0
        self._progress = 0.0
        self._pose_before = self._character.pose_name
        self._on_complete = on_complete

    def stop(self, completed=True):
        """End the behavior.

        Args:
            completed: If True, behavior finished naturally. If False, it was
                       interrupted (e.g., by another action changing the pose).
        """
        if not self._active:
            return

        self._active = False

        # Only restore previous pose if completed naturally
        if self._pose_before and completed:
            self._character.set_pose(self._pose_before)

        self._pose_before = None

        # Store callback before clearing
        callback = self._on_complete
        final_progress = self._progress
        self._on_complete = None

        if callback:
            callback(completed, final_progress)

    def update(self, dt):
        """Update behavior state.

        Override in subclasses to implement phase transitions.

        Args:
            dt: Delta time in seconds.
        """
        if not self._active:
            return
        self._phase_timer += dt

    def draw(self, renderer, char_x, char_y, mirror=False):
        """Draw behavior visual effects.

        Override in subclasses to render bubbles, particles, etc.
        Called by the character's draw method.

        Args:
            renderer: The renderer to draw with.
            char_x: Character's x position on screen.
            char_y: Character's y position.
            mirror: If True, character is facing right (outside scene).
        """
        pass

    def apply_stat_effects(self, context, dt):
        """Apply per-frame stat changes during the behavior.

        Args:
            context: The GameContext to modify.
            dt: Delta time in seconds.
        """
        for stat, rate in self.STAT_EFFECTS.items():
            current = getattr(context, stat, 0)
            new_value = max(0, min(100, current + rate * dt))
            setattr(context, stat, new_value)

    def apply_completion_bonus(self, context, progress=1.0):
        """Apply completion bonus, scaled by progress.

        Args:
            context: The GameContext to modify.
            progress: How much of the behavior was completed (0.0 to 1.0).
        """
        for stat, bonus in self.COMPLETION_BONUS.items():
            current = getattr(context, stat, 0)
            scaled_bonus = bonus * progress
            new_value = max(0, min(100, current + scaled_bonus))
            setattr(context, stat, new_value)

    def mark_triggered(self, current_time):
        """Mark this behavior as having been triggered for cooldown tracking.

        Args:
            current_time: Current elapsed game time in seconds.
        """
        print(f"Triggered behavior: {self.NAME}")
        self._last_trigger_time = current_time
