from enum import Enum
from random import shuffle
from typing import List, Tuple


class Suit(str, Enum):
    """Масти карт"""
    HEARTS = "♥️"
    DIAMONDS = "♦️"
    CLUBS = "♣️"
    SPADES = "♠️"


class Rank(str, Enum):
    """Ранги карт"""
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"


class Card:
    """Класс для одной карты"""

    def __init__(self, suit: Suit, rank: Rank):
        self.suit = suit
        self.rank = rank

    def get_value(self) -> int:
        """Возвращает значение карты"""
        if self.rank in [Rank.JACK, Rank.QUEEN, Rank.KING]:
            return 10
        elif self.rank == Rank.ACE:
            return 11
        else:
            return int(self.rank.value)

    def __str__(self) -> str:
        return f"{self.rank.value}{self.suit.value}"


class Deck:
    """Колода карт"""

    def __init__(self):
        self.cards = []
        self.create_deck()

    def create_deck(self):
        """Создать полную колоду (52 карты)"""
        self.cards = []
        for suit in Suit:
            for rank in Rank:
                self.cards.append(Card(suit, rank))
        shuffle(self.cards)

    def draw_card(self) -> Card:
        """Вытащить карту из колоды"""
        if len(self.cards) < 10:
            self.create_deck()
        return self.cards.pop()


class Hand:
    """Рука игрока/дилера"""

    def __init__(self):
        self.cards: List[Card] = []

    def add_card(self, card: Card):
        """Добавить карту в руку"""
        self.cards.append(card)

    def get_value(self) -> int:
        """Получить общую стоимость руки"""
        total = 0
        aces = 0

        for card in self.cards:
            if card.rank == Rank.ACE:
                aces += 1
            total += card.get_value()

        while total > 21 and aces > 0:
            total -= 10
            aces -= 1

        return total

    def is_bust(self) -> bool:
        """Перебор ли?"""
        return self.get_value() > 21

    def is_blackjack(self) -> bool:
        """Блэкджек ли? (21 с двух карт)"""
        return len(self.cards) == 2 and self.get_value() == 21

    def __str__(self) -> str:
        cards_str = " ".join(str(card) for card in self.cards)
        return f"{cards_str} (Сумма: {self.get_value()})"


class BlackjackGame:
    """Основной класс игры"""

    def __init__(self):
        self.deck = Deck()
        self.player_hand = Hand()
        self.dealer_hand = Hand()
        self.player_bet = 0

    def start_game(self, bet: int) -> str:
        """Начать новую игру"""
        self.player_bet = bet
        self.player_hand = Hand()
        self.dealer_hand = Hand()

        self.player_hand.add_card(self.deck.draw_card())
        self.dealer_hand.add_card(self.deck.draw_card())
        self.player_hand.add_card(self.deck.draw_card())
        self.dealer_hand.add_card(self.deck.draw_card())

        info = f"🎴 Ваша рука: {self.player_hand}\n"
        info += f"🎴 Карта дилера: {self.dealer_hand.cards[0]} + ?\n\n"

        if self.player_hand.is_blackjack():
            info += "🎉 БЛЭКДЖЕК!"
            return info

        info += "Выберите действие: Hit / Stand / Double"
        return info

    def hit(self) -> Tuple[str, bool]:
        """Взять ещё карту"""
        self.player_hand.add_card(self.deck.draw_card())
        info = f"🎴 Ваша рука: {self.player_hand}\n\n"

        if self.player_hand.is_bust():
            info += "💥 Перебор! Вы проиграли."
            return info, True

        info += "Выберите действие: Hit / Stand"
        return info, False

    def double(self) -> Tuple[str, bool]:
        """Удвоить ставку и взять одну карту"""
        self.player_bet *= 2
        self.player_hand.add_card(self.deck.draw_card())

        info = f"🎴 Ваша рука: {self.player_hand}\n"

        if self.player_hand.is_bust():
            info += "💥 Перебор! Дилер выиграл."
            return info, True

        # Автоматический stand после double
        while self.dealer_hand.get_value() < 17:
            self.dealer_hand.add_card(self.deck.draw_card())

        info += f"🎴 Рука дилера: {self.dealer_hand}\n\n"

        player_value = self.player_hand.get_value()
        dealer_value = self.dealer_hand.get_value()

        if self.dealer_hand.is_bust():
            info += "💥 Дилер перебрал! Вы выиграли! 🎉"
        elif player_value > dealer_value:
            info += "Вы выиграли! 🎉"
        elif player_value == dealer_value:
            info += "Ничья. 🤝"
        else:
            info += "Дилер выиграл. 😔"

        return info, True

    def stand(self) -> Tuple[str, int]:
        """Остановиться и ход дилера"""
        while self.dealer_hand.get_value() < 17:
            self.dealer_hand.add_card(self.deck.draw_card())

        info = f"🎴 Ваша рука: {self.player_hand}\n"
        info += f"🎴 Рука дилера: {self.dealer_hand}\n\n"

        player_value = self.player_hand.get_value()
        dealer_value = self.dealer_hand.get_value()

        if self.dealer_hand.is_bust():
            info += "💥 Дилер перебрал! Вы выиграли! 🎉"
            winnings = self.player_bet * 2
        elif player_value > dealer_value:
            info += "Вы выиграли! 🎉"
            winnings = self.player_bet * 2
        elif player_value == dealer_value:
            info += "Ничья. Ставка вернена. 🤝"
            winnings = self.player_bet
        else:
            info += "Дилер выиграл. 😔"
            winnings = 0

        return info, winnings
