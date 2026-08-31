from src.engine import RPGEngine
from src.models import Player


def test_get_stats_and_max_hp():
    engine = RPGEngine()
    player = Player(username="test", str_stat=15, vit=20, int_stat=10, agi=10, sen=10)
    stats = engine.get_stats(player)
    assert stats["str"] == 15
    assert stats["vit"] == 20
    assert engine.get_max_hp(player) == 100 + (20 * 10)
    assert engine.get_max_mp(player) == 150 + (10 * 5)


def test_get_rank():
    engine = RPGEngine()
    assert engine.get_rank(5) == "E"
    assert engine.get_rank(15) == "D"
    assert engine.get_rank(25) == "C"
    assert engine.get_rank(35) == "B"
    assert engine.get_rank(45) == "A"
    assert engine.get_rank(55) == "S"


def test_check_level_up():
    engine = RPGEngine()
    player = Player(username="test", lvl=1, exp=150)
    leveled_up = engine.check_level_up(player)
    assert leveled_up is True
    assert player.lvl == 2
    assert player.stat_points == 5


def test_level_up_over_100():
    engine = RPGEngine()
    assert engine.get_exp_required(99) == 99 * 100
    assert engine.get_exp_required(100) == 100 * 100 * 2
    player = Player(username="test", lvl=100, exp=20000)
    leveled_up = engine.check_level_up(player)
    assert leveled_up is True
    assert player.lvl == 101


def test_achievements_and_titles():
    engine = RPGEngine()
    player = Player(username="test", gold=100, title="shadow_monarch")
    stats = engine.get_stats(player)
    # shadow_monarch gives +25 str, +15 agi, +20 vit
    assert stats["str"] == 10 + 25
    assert stats["vit"] == 10 + 20

    ach = engine.unlock_achievement(player, "first_hunt")
    assert ach is not None
    assert "first_hunt" in player.achievements
    assert player.gold == 100 + 100

    # Unlocking same achievement again should return None
    ach_duplicate = engine.unlock_achievement(player, "first_hunt")
    assert ach_duplicate is None
