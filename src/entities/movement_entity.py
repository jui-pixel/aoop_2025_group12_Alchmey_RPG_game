            if magnitude > 0:
                dx /= magnitude
                dy /= magnitude
            self.velocity = (dx * self.max_speed, dy * self.max_speed)
        else:
            lerp_factor = 0.1
            vx = self.velocity[0] * (1 - lerp_factor)
            vy = self.velocity[1] * (1 - lerp_factor)
            self.velocity = (vx, vy)
            self.displacement = (0.0, 0.0)
            if math.sqrt(vx**2 + vy**2) < self.max_speed * 0.05:
                self.velocity = (0.0, 0.0)

        new_x = self.x + self.velocity[0] * dt
        new_y = self.y + self.velocity[1] * dt
        
        if not self._pass_wall:
            tile_x, tile_y = int(new_x // TILE_SIZE), int(new_y // TILE_SIZE)
            x_valid = 0 <= tile_x < self.dungeon.grid_width
            y_valid = 0 <= tile_y < self.dungeon.grid_height
            if x_valid and y_valid:
                tile = self.dungeon.dungeon_tiles[tile_y][tile_x]
                if tile in PASSABLE_TILES:
                    self.set_position(new_x, new_y)
                else:
                    x_allowed = x_valid and self.dungeon.dungeon_tiles[int(self.y // TILE_SIZE)][tile_x] in PASSABLE_TILES
                    y_allowed = y_valid and self.dungeon.dungeon_tiles[tile_y][int(self.x // TILE_SIZE)] in PASSABLE_TILES
                    if x_allowed:
                        self.set_position(new_x, self.y)
                        self.velocity = (self.velocity[0], 0.0)
                    if y_allowed:
                        self.set_position(self.x, new_y)
                        self.velocity = (0.0, self.velocity[1])
                    if not (x_allowed or y_allowed):
                        self.velocity = (0.0, 0.0)
        else:
            self.set_position(new_x, new_y)
        
    def update(self, dt: float, current_time: float) -> None:
        """Update movement entity position based on velocity."""  # 無變動
        if self.can_move:
            self.move(self.displacement[0], self.displacement[1], dt)