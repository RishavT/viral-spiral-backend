"""All models related to cards"""
import peewee
from .base import InGameModel
from .player import Player
from .counters import AffinityTopic, Color


class Card(InGameModel):
    """Represents a card in the game"""

    title = peewee.CharField()
    description = peewee.TextField()
    affinity_towards = peewee.ForeignKeyField(AffinityTopic)
    affinity_count = peewee.IntegerField()  # Can be +1 or -1

    bias_against = peewee.ForeignKeyField(Color)

    bias_history = peewee.ManyToManyField(Color)

    original_player = peewee.ForeignKeyField(Player)

    # # IntegerField to denote whether this card is the currently active card in
    # # a round or not. If this is 0, it means it is the active card
    # _is_current_int = peewee.IntegerField(unique=True, default=-1)

    # def is_active(self):
    #     return self._is_current_int == 0

    # @classmethod
    # def get_active_card(cls, cards):
    #     """cards should be a query selector"""
    #     return cards.where(cls._is_current_int == 0).first()

    def add_bias(self, against: Color):
        """Adds a bias to this card"""
        if self.bias_against:
            self.bias_history.add(self.bias_against)
        self.bias_against = against
        self.save()

    def draw(self, player: Player):
        """Creates and returns a card instance. Does not affect the player
        score"""
        card_instance = CardInstance(
            card=self,
            from_=None,
            player=player,
        )
        card_instance.save()
        self.original_player = player
        self.save()
        player.event_receive_card(card_instance)
        return card_instance


class CardInstance(InGameModel):
    """Stores as instance of a passed / drawn card.

    If the card is drawn, from_ will be null.

    Else, from_ will be a reference to a passed card

    to_ will be the player that this card has gone to
    """

    STATUS_PASSED = "passed"
    STATUS_HOLDING = "holding"

    card = peewee.ForeignKeyField(Card)
    from_ = peewee.ForeignKeyField("self", null=True, unique=False, backref="to_")
    player = peewee.ForeignKeyField(
        Player, null=False, unique=False, backref="card_instances"
    )

    class Meta:
        # Unique together
        indexes = ((("card_id", "player_id"), True),)

    @property
    def status(self):
        """Status of this card instance - can be "passed" or "holding" """
        if self.to_:
            return self.STATUS_PASSED
        else:
            return self.STATUS_HOLDING
