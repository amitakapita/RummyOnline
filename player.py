class Player(object):
    def __init__(self, color, conn, player_name, creator):
        self.color = color
        self.is_my_turn = False
        self.conn = conn
        self.player_name = player_name
        self.creator = creator

    def change_color(self, new_color_player):
        if self.color != new_color_player:
            self.color = new_color_player

    def __repr__(self):
        return f"{self.color}, {self.is_my_turn}, {self.conn}, {self.player_name}, {self.creator}"
