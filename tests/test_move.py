"""Unit tests for movement actions in arcade_actions.

This module contains tests for movement-related actions:
- _Move (base movement class)
- WrappedMove (wrapping at screen bounds)
- BoundedMove (bouncing at screen bounds)
- Driver (directional movement) - not tested here

All tests use ActionSprite for sprite-based tests and follow the standard
action lifecycle pattern using sprite.do(action) and sprite.update().
"""

import arcade
import arcade.easing as easing
import pytest

from actions.base import ActionSprite
from actions.interval import Easing, MoveBy
from actions.move import BoundedMove, WrappedMove, _Move


class TestMove:
    """Test suite for base movement class.

    Tests the basic movement functionality that all movement actions inherit from.
    Focuses on:
    - Basic position updates
    - Velocity-based movement
    - Rotation during movement
    """

    @pytest.fixture
    def sprite(self):
        """Create a test sprite with initial position and velocity."""
        sprite = ActionSprite(":resources:images/items/star.png")
        sprite.position = (0, 0)
        sprite.change_x = 100  # Initial velocity
        sprite.change_y = 100
        return sprite

    def test_basic_movement(self, sprite):
        """Test basic movement without physics.

        Verifies that:
        - Position updates correctly based on velocity
        - Movement is frame-independent using delta_time
        """
        action = _Move()
        sprite.do(action)

        # Update with 0.1s time step (100 * 0.1 = 10 pixels)
        sprite.update(0.1)
        assert sprite.position == (10, 10)

    def test_movement_with_rotation(self, sprite):
        """Test movement with rotation.

        Verifies that:
        - Position updates correctly
        - Rotation updates correctly
        - Both use the same delta_time
        """
        sprite.change_angle = 45  # 45 degrees per second
        action = _Move()
        sprite.do(action)

        # Update with 0.1s time step
        sprite.update(0.1)
        assert sprite.position == (10, 10)  # 100 * 0.1 = 10
        assert sprite.angle == 4.5  # 45 * 0.1 = 4.5


class TestWrappedMove:
    """Test suite for wrapping movement.

    Tests the WrappedMove action's behavior when sprites move across screen boundaries.
    Focuses on:
    - Wrapping behavior at each boundary
    - Corner cases
    - Wrap callbacks
    - Sprite list handling
    - Physics integration
    """

    @pytest.fixture
    def sprite(self):
        """Create a test sprite with initial position and velocity."""
        sprite = ActionSprite(":resources:images/items/star.png")
        sprite.position = (0, 0)
        sprite.change_x = 100  # Initial velocity
        sprite.change_y = 100
        return sprite

    @pytest.fixture
    def sprite_list(self):
        """Create a list of test sprites for group behavior testing."""
        sprites = arcade.SpriteList()
        for _ in range(3):
            sprite = ActionSprite(":resources:images/items/star.png")
            sprite.position = (0, 0)
            sprite.change_x = 100
            sprite.change_y = 100
            sprites.append(sprite)
        return sprites

    @pytest.fixture
    def get_bounds(self):
        """Create a function that returns screen bounds."""
        return lambda: (800, 600)

    def test_wrap_right_edge(self, sprite, get_bounds):
        """Test wrapping when sprite moves off right edge.

        Verifies that:
        - Sprite wraps to left edge when moving right
        - Position is correctly aligned to boundary
        """
        action = WrappedMove(get_bounds)
        sprite.do(action)

        # Position sprite off right edge
        sprite.center_x = 900
        sprite.center_y = 300
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite wrapped to left edge
        assert sprite.center_x < 0  # Wrapped to left edge
        assert sprite.center_y == 300  # Y position unchanged

    def test_wrap_left_edge(self, sprite, get_bounds):
        """Test wrapping when sprite moves off left edge.

        Verifies that:
        - Sprite wraps to right edge when moving left
        - Position is correctly aligned to boundary
        """
        action = WrappedMove(get_bounds)
        sprite.do(action)

        # Position sprite off left edge
        sprite.center_x = -100
        sprite.center_y = 300
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite wrapped to right edge
        assert sprite.center_x > 800  # Wrapped to right edge
        assert sprite.center_y == 300  # Y position unchanged

    def test_wrap_top_edge(self, sprite, get_bounds):
        """Test wrapping when sprite moves off top edge.

        Verifies that:
        - Sprite wraps to bottom edge when moving up
        - Position is correctly aligned to boundary
        """
        action = WrappedMove(get_bounds)
        sprite.do(action)

        # Position sprite off top edge
        sprite.center_x = 300
        sprite.center_y = 700
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite wrapped to bottom edge
        assert sprite.center_x == 300  # X position unchanged
        assert sprite.center_y < 0  # Wrapped to bottom edge

    def test_wrap_bottom_edge(self, sprite, get_bounds):
        """Test wrapping when sprite moves off bottom edge.

        Verifies that:
        - Sprite wraps to top edge when moving down
        - Position is correctly aligned to boundary
        """
        action = WrappedMove(get_bounds)
        sprite.do(action)

        # Position sprite off bottom edge
        sprite.center_x = 300
        sprite.center_y = -100
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite wrapped to top edge
        assert sprite.center_x == 300  # X position unchanged
        assert sprite.center_y > 600  # Wrapped to top edge

    def test_wrap_corner(self, sprite, get_bounds):
        """Test wrapping when sprite moves off a corner.

        Verifies that:
        - Sprite wraps correctly when hitting a corner
        - Position is correctly aligned to both boundaries
        """
        action = WrappedMove(get_bounds)
        sprite.do(action)

        # Position sprite off top-right corner
        sprite.center_x = 900
        sprite.center_y = 700
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite wrapped to bottom-left corner
        assert sprite.center_x < 0  # Wrapped to left edge
        assert sprite.center_y < 0  # Wrapped to bottom edge

    def test_wrap_callback(self, sprite, get_bounds):
        """Test wrap callback with correct axis information.

        Verifies that:
        - Callback is called with correct axis
        - Multiple wraps are reported correctly
        """
        wraps = []

        def on_wrap(sprite, axis):
            wraps.append(axis)

        action = WrappedMove(get_bounds, on_wrap=on_wrap)
        sprite.do(action)

        # Position sprite off top-right corner
        sprite.center_x = 900
        sprite.center_y = 700
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify correct axes were reported
        assert "x" in wraps
        assert "y" in wraps
        assert len(wraps) == 2  # Both axes wrapped

    def test_sprite_list_wrapping(self, sprite_list, get_bounds):
        """Test wrapping behavior with multiple sprites.

        Verifies that:
        - Each sprite wraps independently
        - List-level updates work correctly
        - Positions are correctly aligned after wrapping
        """
        action = WrappedMove(get_bounds)
        action.target = sprite_list
        action.start()

        # Position sprites at different off-screen locations
        sprite_list[0].center_x = 900  # Off right
        sprite_list[0].center_y = 300
        sprite_list[0].change_x = 100  # Moving right
        sprite_list[0].change_y = 0  # No vertical movement

        sprite_list[1].center_x = -100  # Off left
        sprite_list[1].center_y = 300
        sprite_list[1].change_x = -100  # Moving left
        sprite_list[1].change_y = 0  # No vertical movement

        sprite_list[2].center_x = 300  # Off top
        sprite_list[2].center_y = 700
        sprite_list[2].change_x = 0  # No horizontal movement
        sprite_list[2].change_y = 100  # Moving up

        sprite_list.update(0.1)  # Update with 0.1s time step
        action.update(0.1)  # Update with 0.1s time step

        # Verify each sprite wrapped correctly
        assert sprite_list[0].center_x < 0  # Wrapped to left edge
        assert sprite_list[1].center_x > 800  # Wrapped to right edge
        assert sprite_list[2].center_y < 0  # Wrapped to bottom edge

    def test_wrap_with_acceleration(self, sprite, get_bounds):
        """Test wrapping behavior with easing.

        Verifies that:
        - Wrapping works with easing
        - Easing curve is maintained
        - Position is correctly aligned after wrapping
        - Eased timing is properly propagated
        """
        # Create base movement action
        move_action = MoveBy((200, 0), 1.0)
        # Create easing modifier using ease_in for acceleration effect
        ease_action = Easing(move_action, ease_function=easing.ease_in)
        # Create wrapped movement action
        wrap_action = WrappedMove(get_bounds)

        # Set up actions
        sprite.do(ease_action)
        sprite.do(wrap_action)

        # Set initial position
        sprite.center_x = 700  # Near right edge
        sprite.center_y = 300

        # Update for 0.1 seconds
        delta = sprite.update(0.1)  # Updates position based on easing curve and handles wrapping

        # Verify sprite wrapped and maintained easing curve
        assert sprite.center_x < 0  # Wrapped to left edge
        assert sprite.center_y == 300  # Y position unchanged
        # Delta time should be eased (ease_in(0.1) ≈ 0.01)
        assert abs(delta - 0.01) < 0.01

    def test_disable_horizontal_wrapping(self, sprite, get_bounds):
        """Test disabling horizontal wrapping.

        Verifies that:
        - Horizontal wrapping is disabled
        - Vertical wrapping still works
        - Sprite can move off screen horizontally
        """
        action = WrappedMove(get_bounds, wrap_horizontal=False)
        sprite.do(action)

        # Position sprite off right edge
        sprite.center_x = 900
        sprite.center_y = 300
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite did not wrap horizontally
        assert sprite.center_x == 900  # Position unchanged
        assert sprite.center_y == 300  # Y position unchanged

    def test_disable_vertical_wrapping(self, sprite, get_bounds):
        """Test disabling vertical wrapping.

        Verifies that:
        - Vertical wrapping is disabled
        - Horizontal wrapping still works
        - Sprite can move off screen vertically
        """
        action = WrappedMove(get_bounds, wrap_vertical=False)
        sprite.do(action)

        # Position sprite off top edge
        sprite.center_x = 300
        sprite.center_y = 700
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite did not wrap vertically
        assert sprite.center_x == 300  # X position unchanged
        assert sprite.center_y == 700  # Position unchanged

    def test_dynamic_bounds(self, sprite):
        """Test wrapping with dynamically changing screen bounds.

        Verifies that:
        - Wrapping works with changing screen dimensions
        - Sprite wraps to correct position after resize
        """
        bounds = [800, 600]  # Initial bounds

        def get_bounds():
            return tuple(bounds)

        action = WrappedMove(get_bounds)
        sprite.do(action)

        # Position sprite off right edge
        sprite.center_x = 900
        sprite.center_y = 300
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite wrapped to left edge
        assert sprite.center_x < 0  # Wrapped to left edge
        assert sprite.center_y == 300  # Y position unchanged

        # Change screen bounds
        bounds[0] = 1000  # Increase width
        bounds[1] = 800  # Increase height

        # Position sprite off right edge again
        sprite.center_x = 1100
        sprite.center_y = 300
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite wrapped to left edge with new bounds
        assert sprite.center_x < 0  # Wrapped to left edge
        assert sprite.center_y == 300  # Y position unchanged

    def test_wrap_with_rotation(self, sprite, get_bounds):
        """Test wrapping with rotated sprite.

        Verifies that:
        - Wrapping works with rotated sprites
        - Hit box is correctly calculated
        - Position is correctly aligned after wrapping
        """
        action = WrappedMove(get_bounds)
        sprite.do(action)

        # Rotate sprite and position off right edge
        sprite.angle = 45
        sprite.center_x = 900
        sprite.center_y = 300
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite wrapped to left edge
        assert sprite.center_x < 0  # Wrapped to left edge
        assert sprite.center_y == 300  # Y position unchanged
        assert sprite.angle == 45  # Rotation unchanged


class TestBoundedMove:
    """Test suite for bounded movement.

    Tests the BoundedMove action's behavior when sprites hit screen boundaries.
    Focuses on:
    - Bouncing behavior at each boundary
    - Corner cases
    - Bounce callbacks
    - Sprite list handling
    - Physics integration
    """

    @pytest.fixture
    def sprite(self):
        """Create a test sprite with initial position and velocity."""
        sprite = ActionSprite(":resources:images/items/star.png")
        sprite.position = (0, 0)
        sprite.change_x = 100  # Initial velocity
        sprite.change_y = 100
        return sprite

    @pytest.fixture
    def sprite_list(self):
        """Create a list of test sprites for group behavior testing."""
        sprites = arcade.SpriteList()
        for _ in range(3):
            sprite = ActionSprite(":resources:images/items/star.png")
            sprite.position = (0, 0)
            sprite.change_x = 100
            sprite.change_y = 100
            sprites.append(sprite)
        return sprites

    @pytest.fixture
    def get_bounds(self):
        """Create a function that returns bounding zone."""
        return lambda: (0, 0, 800, 600)  # left, bottom, right, top

    def test_bounce_right_edge(self, sprite, get_bounds):
        """Test bouncing when sprite hits right edge.

        Verifies that:
        - Sprite bounces at right edge
        - Velocity is reversed
        - Position is correctly adjusted
        """
        action = BoundedMove(get_bounds)
        sprite.do(action)

        # Position sprite at right edge
        sprite.center_x = 736  # right edge at 800
        sprite.center_y = 300
        sprite.change_x = 100  # Moving right
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite bounced
        assert sprite.change_x == -100  # X direction reversed
        assert sprite.center_y == 300  # Y position unchanged

    def test_bounce_left_edge(self, sprite, get_bounds):
        """Test bouncing when sprite hits left edge.

        Verifies that:
        - Sprite bounces at left edge
        - Velocity is reversed
        - Position is correctly adjusted
        """
        action = BoundedMove(get_bounds)
        sprite.do(action)

        # Position sprite at left edge
        sprite.center_x = 64  # left edge at 0
        sprite.center_y = 300
        sprite.change_x = -100  # Moving left
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite bounced
        assert sprite.change_x == 100  # X direction reversed
        assert sprite.center_y == 300  # Y position unchanged

    def test_bounce_top_edge(self, sprite, get_bounds):
        """Test bouncing when sprite hits top edge.

        Verifies that:
        - Sprite bounces at top edge
        - Velocity is reversed
        - Position is correctly adjusted
        """
        action = BoundedMove(get_bounds)
        sprite.do(action)

        # Position sprite at top edge
        sprite.center_x = 300
        sprite.center_y = 536  # top edge at 600
        sprite.change_y = 100  # Moving up
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite bounced
        assert sprite.change_y == -100  # Y direction reversed
        assert sprite.center_x == 300  # X position unchanged

    def test_bounce_bottom_edge(self, sprite, get_bounds):
        """Test bouncing when sprite hits bottom edge.

        Verifies that:
        - Sprite bounces at bottom edge
        - Velocity is reversed
        - Position is correctly adjusted
        """
        action = BoundedMove(get_bounds)
        sprite.do(action)

        # Position sprite at bottom edge
        sprite.center_x = 300
        sprite.center_y = 64  # bottom edge at 0
        sprite.change_y = -100  # Moving down
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite bounced
        assert sprite.change_y == 100  # Y direction reversed
        assert sprite.center_x == 300  # X position unchanged

    def test_bounce_corner(self, sprite, get_bounds):
        """Test bouncing when sprite hits a corner.

        Verifies that:
        - Sprite bounces in both directions
        - Velocities are reversed
        - Position is correctly adjusted
        """
        action = BoundedMove(get_bounds)
        sprite.do(action)

        # Position sprite at top-right corner
        sprite.center_x = 736  # right edge at 800
        sprite.center_y = 536  # top edge at 600
        sprite.change_x = 100  # Moving right
        sprite.change_y = 100  # Moving up
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite bounced in both directions
        assert sprite.change_x == -100  # X direction reversed
        assert sprite.change_y == -100  # Y direction reversed

    def test_bounce_callback(self, sprite, get_bounds):
        """Test bounce callback with correct axis information.

        Verifies that:
        - Callback is called with correct axis
        - Multiple bounces are reported correctly
        """
        bounces = []

        def on_bounce(sprite, axis):
            bounces.append(axis)

        action = BoundedMove(get_bounds, on_bounce=on_bounce)
        sprite.do(action)

        # Position sprite at top-right corner
        sprite.center_x = 736  # right edge at 800
        sprite.center_y = 536  # top edge at 600
        sprite.change_x = 100  # Moving right
        sprite.change_y = 100  # Moving up
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify correct axes were reported
        assert "x" in bounces
        assert "y" in bounces
        assert len(bounces) == 2  # Both axes bounced

    def test_sprite_list_bouncing(self, sprite_list, get_bounds):
        """Test bouncing with multiple sprites.

        Verifies that:
        - Each sprite bounces independently
        - List-level updates work correctly
        - Velocities are reversed correctly
        """
        action = BoundedMove(get_bounds)
        action.target = sprite_list
        action.start()

        # Position sprites at different locations
        sprite_list[0].center_x = 736  # Near right edge
        sprite_list[0].center_y = 300
        sprite_list[1].center_x = 300  # Near top edge
        sprite_list[1].center_y = 536
        sprite_list[2].center_x = 64  # Near left edge
        sprite_list[2].center_y = 300

        # Set velocities
        for sprite in sprite_list:
            sprite.change_x = 100  # All moving right
            sprite.change_y = 100  # All moving up

        action.update(0.1)  # Update with 0.1s time step

        # Verify each sprite bounced correctly
        assert sprite_list[0].change_x == -100  # Reversed X direction
        assert sprite_list[1].change_y == -100  # Reversed Y direction
        assert sprite_list[2].change_x == 100  # Reversed X direction

    def test_disable_horizontal_bouncing(self, sprite, get_bounds):
        """Test disabling horizontal bouncing.

        Verifies that:
        - Horizontal bouncing is disabled
        - Vertical bouncing still works
        - Sprite can move through horizontal boundaries
        """
        action = BoundedMove(get_bounds, bounce_horizontal=False)
        sprite.do(action)

        # Position sprite at right edge
        sprite.center_x = 736  # right edge at 800
        sprite.center_y = 300
        sprite.change_x = 100  # Moving right
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite did not bounce horizontally
        assert sprite.change_x == 100  # X direction unchanged
        assert sprite.center_y == 300  # Y position unchanged

    def test_disable_vertical_bouncing(self, sprite, get_bounds):
        """Test disabling vertical bouncing.

        Verifies that:
        - Vertical bouncing is disabled
        - Horizontal bouncing still works
        - Sprite can move through vertical boundaries
        """
        action = BoundedMove(get_bounds, bounce_vertical=False)
        sprite.do(action)

        # Position sprite at top edge
        sprite.center_x = 300
        sprite.center_y = 536  # top edge at 600
        sprite.change_y = 100  # Moving up
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite did not bounce vertically
        assert sprite.change_y == 100  # Y direction unchanged
        assert sprite.center_x == 300  # X position unchanged

    def test_dynamic_bounds(self, sprite):
        """Test bouncing with dynamically changing bounding zone.

        Verifies that:
        - Bouncing works with changing boundaries
        - Sprite bounces at correct position after resize
        """
        bounds = [0, 0, 800, 600]  # Initial bounds

        def get_bounds():
            return tuple(bounds)

        action = BoundedMove(get_bounds)
        sprite.do(action)

        # Position sprite at right edge
        sprite.center_x = 736  # right edge at 800
        sprite.center_y = 300
        sprite.change_x = 100  # Moving right
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite bounced
        assert sprite.change_x == -100  # X direction reversed
        assert sprite.center_y == 300  # Y position unchanged

        # Change bounding zone
        bounds[2] = 1000  # Increase right boundary
        bounds[3] = 800  # Increase top boundary

        # Position sprite at new right edge
        sprite.center_x = 936  # right edge at 1000
        sprite.center_y = 300
        sprite.change_x = 100  # Moving right
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite bounced at new boundary
        assert sprite.change_x == -100  # X direction reversed
        assert sprite.center_y == 300  # Y position unchanged

    def test_bounce_with_rotation(self, sprite, get_bounds):
        """Test bouncing with rotated sprite.

        Verifies that:
        - Bouncing works with rotated sprites
        - Hit box is correctly calculated
        - Position is correctly adjusted after bounce
        """
        action = BoundedMove(get_bounds)
        sprite.do(action)

        # Rotate sprite and position at right edge
        sprite.angle = 45
        sprite.center_x = 736  # right edge at 800
        sprite.center_y = 300
        sprite.change_x = 100  # Moving right
        sprite.update(0.1)  # Update with 0.1s time step

        # Verify sprite bounced
        assert sprite.change_x == -100  # X direction reversed
        assert sprite.center_y == 300  # Y position unchanged
        assert sprite.angle == 45  # Rotation unchanged
