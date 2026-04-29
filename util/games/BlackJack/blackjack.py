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
        if self.rank in ["J", "Q", "K"]:
            return 10
        elif self.rank == "A":
            return 11  # По умолчанию туз = 11
        else:
            return int(self.rank)

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"


class Deck:
    """Колода карт"""

    def __init__(self):
        self.cards = []
        self.create_deck()

    def create_deck(self):
        """Создать полную колоду (52 карты)"""
        for suit in Suit:
            for rank in Rank:
                self.cards.append(Card(suit, rank))
        shuffle(self.cards)

    def draw_card(self) -> Card:
        """Вытащить карту из колоды"""
        if len(self.cards) < 10:  # Если карт осталось мало, пересоздаём колоду
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

        # Считаем сумму (все тузы считаются как 11)
        for card in self.cards:
            if card.rank == "A":
                aces += 1
            total += card.get_value()

        # Если сумма больше 21 и есть тузы, считаем их как 1
        while total > 21 and aces > 0:
            total -= 10  # Туз 11 становится тузом 1 (11 - 10 = 1)
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

        # Раздаём по 2 карты
        self.player_hand.add_card(self.deck.draw_card())
        self.dealer_hand.add_card(self.deck.draw_card())
        self.player_hand.add_card(self.deck.draw_card())
        self.dealer_hand.add_card(self.deck.draw_card())

        info = f"🎴 Ваша рука: {self.player_hand}\n"
        info += f"🎴 Карта дилера: {self.dealer_hand.cards[0]} + ?\n\n"

        if self.player_hand.is_blackjack():
            info += "🎉 БЛЭКДЖЕК! Вы выиграли!"
            return info

        info += "Выберите действие: Hit / Stand / Double"
        return info

    def hit(self) -> Tuple[str, bool]:
        """Взять ещё карту"""
        self.player_hand.add_card(self.deck.draw_card())
        info = f"🎴 Ваша рука: {self.player_hand}\n\n"

        if self.player_hand.is_bust():
            info += "💥 Перебор! Вы проиграли."
            return info, True  # Игра закончена

        info += "Выберите действие: Hit / Stand"
        return info, False

    def stand(self) -> Tuple[str, int]:
        """Остановиться и ход дилера"""
        # Ход дилера
        while self.dealer_hand.get_value() < 17:
            self.dealer_hand.add_card(self.deck.draw_card())

        info = f"🎴 Ваша рука: {self.player_hand}\n"
        info += f"🎴 Рука дилера: {self.dealer_hand}\n\n"

        # Определяем результат
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

    def double_down(self) -> Tuple[str, int]:
        """Удвоить ставку и взять одну карту"""
        self.player_bet *= 2
        self.player_hand.add_card(self.deck.draw_card())

        if self.player_hand.is_bust():
            info = f"🎴 Ваша рука: {self.player_hand}\n\n"
            info += "💥 Перебор! Вы проиграли."
            return info, 0

        # Сразу ход дилера (после double down обычно стоп)
        return self.stand()
