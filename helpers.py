import json


class QuestInfo():
    # This is just a blank class so I can pass Quest data as a single
    # object.
    def __init__(
            self,
            quest_title: str,
            contractor: str,
            description: str,
            reward: str,
            embed_colour: str,
            thread_id: int,
            quest_role_id: int,
            pin_message_id: int,
            players: str = None) -> None:
        self.quest_title = quest_title
        self.contractor = contractor
        self.description = description
        self.reward = reward
        self.embed_colour = embed_colour
        self.thread_id = thread_id
        self.quest_role_id = quest_role_id
        self.pin_message_id = pin_message_id
        if players is not None:
            self._players = json.loads(players)
        else:
            self._players = []

    @property
    def players(self) -> str:
        return json.dumps(self._players)

    def add_player(self, member: int) -> None:
        """Adds a player to the list.

        Args:
            member (int): player ID
        """
        self._players.append(member)

    def remove_player(self, member: int) -> None:
        """Removes a player from the list

        Args:
            member (int): player ID
        """
        try:
            self._players.remove(member)
        except ValueError:
            print(
                f"can't remove player with id {member} from quest {self.quest_title} as they don't exist in the list")
