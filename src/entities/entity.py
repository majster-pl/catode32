class Entity:
    """Base class for all game entities."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.visible = True

    def update(self, dt):
        """Update entity logic. Override in subclasses."""
        pass

    def draw(self, renderer):
        """Draw the entity. Override in subclasses."""
        pass
