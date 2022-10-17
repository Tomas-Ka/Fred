import json
import discord

class QuestInfo():
    # This is just a blank class so I more easily can pass Quest data between
    # objects
    def __init__(
            self,
            quest_title: str,
            contractor: str,
            description: str,
            reward: str,
            embed_colour: str,
            thread_id: int,
            quest_role_id: int,
            player_message: discord.Message,
            pin_message_id: int,
            players: str = None) -> None:
        self.quest_title = quest_title
        self.contractor = contractor
        self.description = description
        self.reward = reward
        self.embed_colour = embed_colour
        self.thread_id = thread_id
        self.quest_role_id = quest_role_id
        self.player_message = player_message
        self.pin_message_id = pin_message_id
        if players is not None:
            self.players = json.loads(players)
        else:
            self.players = []

    # adds a player (in the form of a member object) to the list
    def add_player(self, member: discord.Member) -> None:
        self.players.append(member)

    # removes a player (as a member object) from the list
    def remove_player(self, member: discord.Member) -> None:
        self.players.remove(member)

    def get_players_json(self) -> str:
        return json.dumps(self._players)