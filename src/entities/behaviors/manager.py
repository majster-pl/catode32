"""Behavior manager for coordinating character behaviors."""

from entities.behaviors.eating import EatingBehavior
from entities.behaviors.idle import IdleBehavior
from entities.behaviors.sleeping import SleepingBehavior
from entities.behaviors.investigating import InvestigatingBehavior
from entities.behaviors.playing import PlayingBehavior
from entities.behaviors.stretching import StretchingBehavior
from entities.behaviors.affection import AffectionBehavior
from entities.behaviors.attention import AttentionBehavior
from entities.behaviors.snacking import SnackingBehavior


class BehaviorManager:
    """Manages automatic behavior selection and triggering.

    Owns references to all behaviors and handles:
    - Creating and registering all behaviors
    - Automatic selection based on stats
    - Override mechanism via context.override_next_behavior
    - Cooldown tracking
    - Stat application during behaviors
    """

    def __init__(self, character, context):
        """Initialize the behavior manager and create all behaviors.

        Args:
            character: The CharacterEntity that owns this manager.
            context: The GameContext for stat checks and overrides.
        """
        self._character = character
        self._context = context
        self._current_time = 0.0  # Elapsed game time

        # Create all behaviors
        self._behaviors = {}  # name -> behavior instance
        self._idle_behavior = None

        self._create_behaviors()

        # Selection state
        self._check_interval = 15.0  # Check for new behavior every 5 seconds
        self._time_since_check = 0.0

    def _create_behaviors(self):
        """Create and register all behavior instances."""
        character = self._character

        # Create behaviors
        eating = EatingBehavior(character)
        idle = IdleBehavior(character)
        sleeping = SleepingBehavior(character)
        investigating = InvestigatingBehavior(character)
        playing = PlayingBehavior(character)
        stretching = StretchingBehavior(character)
        affection = AffectionBehavior(character)
        attention = AttentionBehavior(character)
        snacking = SnackingBehavior(character)

        # Register them
        self._register(eating)
        self._register(idle, is_idle=True)
        self._register(sleeping)
        self._register(investigating)
        self._register(playing)
        self._register(stretching)
        self._register(affection)
        self._register(attention)
        self._register(snacking)

        # Expose on character for direct access (e.g., character.eating)
        character.eating = eating
        character.idle = idle
        character.sleeping = sleeping
        character.investigating = investigating
        character.playing = playing
        character.stretching = stretching
        character.affection = affection
        character.attention = attention
        character.snacking = snacking

    def _register(self, behavior, is_idle=False):
        """Register a behavior with the manager.

        Args:
            behavior: The behavior instance to register.
            is_idle: If True, this is the special idle/default behavior.
        """
        self._behaviors[behavior.NAME] = behavior
        if is_idle:
            self._idle_behavior = behavior

    @property
    def active_behavior(self):
        """Return the currently active behavior, or None.

        Prioritizes non-idle behaviors over idle.
        """
        # First pass: look for any active non-idle behavior
        for behavior in self._behaviors.values():
            if behavior.active and behavior != self._idle_behavior:
                return behavior
        # Second pass: check if idle is active
        if self._idle_behavior and self._idle_behavior.active:
            return self._idle_behavior
        return None

    def get_behavior(self, name):
        """Get a behavior by name.

        Args:
            name: The behavior's NAME attribute.

        Returns:
            The behavior instance, or None if not found.
        """
        return self._behaviors.get(name)

    def trigger(self, name, **kwargs):
        """Manually trigger a behavior by name.

        Args:
            name: The behavior's NAME to trigger.
            **kwargs: Additional arguments to pass to start().

        Returns:
            True if the behavior was started, False otherwise.
        """
        # Stop any active behavior first
        active = self.active_behavior
        if active:
            active.stop(completed=False)

        behavior = self._behaviors.get(name)
        if behavior:
            behavior.mark_triggered(self._current_time)
            behavior.start(**kwargs)
            return True
        return False

    def update(self, dt):
        """Update behaviors and check for automatic triggers.

        Args:
            dt: Delta time in seconds.
        """
        self._current_time += dt

        # Check if a non-idle behavior became active (started externally)
        # If so, stop idle to prevent conflicts
        active = self.active_behavior
        if active and active != self._idle_behavior:
            if self._idle_behavior and self._idle_behavior.active:
                self._idle_behavior.stop(completed=False)

        # Update active behavior
        if active:
            active.update(dt)
            if self._context:
                active.apply_stat_effects(self._context, dt)
            # Only return early for non-idle behaviors
            # Idle should still allow automatic trigger checks
            if active != self._idle_behavior:
                return

        # No active behavior - check for override first
        if self._context:
            override = getattr(self._context, 'override_next_behavior', None)
            if override:
                self._context.override_next_behavior = None
                if self.trigger(override):
                    return

        # Periodic check for automatic behavior
        self._time_since_check += dt
        if self._time_since_check >= self._check_interval:
            self._time_since_check = 0.0
            if self._try_automatic_trigger():
                return

        # Fall back to idle if nothing else is happening
        if self._idle_behavior and not self._idle_behavior.active:
            self._idle_behavior.start()

    def _try_automatic_trigger(self):
        """Try to trigger a behavior automatically based on stats.

        Returns:
            True if a behavior was triggered, False otherwise.
        """
        print("Checking automatic trigger...")
        if not self._context:
            print("No context?")
            return False

        eligible = []

        for behavior in self._behaviors.values():
            # Skip idle - it's handled separately as fallback
            if behavior == self._idle_behavior:
                continue
            if behavior.can_trigger(self._context, self._current_time):
                eligible.append(behavior)

        if not eligible:
            print("No eligible behavioral changes. Staying idle.")
            return False

        # Sort by priority (lower = higher priority)
        eligible.sort(key=lambda b: b.PRIORITY)

        # Trigger highest priority
        best = eligible[0]

        # Stop idle if it's running
        if self._idle_behavior and self._idle_behavior.active:
            self._idle_behavior.stop(completed=False)

        best.mark_triggered(self._current_time)
        best.start(on_complete=self._on_behavior_complete)
        return True

    def _on_behavior_complete(self, completed, progress):
        """Called when a behavior completes.

        Args:
            completed: Whether the behavior finished naturally.
            progress: How much of the behavior was completed (0.0 to 1.0).
        """
        # Apply completion bonus if completed naturally
        if completed and self._context:
            # Find the behavior that just completed
            for behavior in self._behaviors.values():
                # The behavior that just called us should have _on_complete = None now
                # This is a bit indirect but works
                if not behavior.active and behavior.COMPLETION_BONUS:
                    behavior.apply_completion_bonus(self._context, progress)
                    break
