import asyncio
import os

from src.models import DBManager, Player


def test_pvp_wins_and_leaderboard():
    async def run_test():
        db_path = "test_pvp.db"
        if os.path.exists(db_path):
            os.remove(db_path)

        db = DBManager(db_path=db_path)
        await db.init_db()

        p1 = Player(username="player1", pvp_wins=5)
        p2 = Player(username="player2", pvp_wins=12)

        await db.save(p1)
        await db.save(p2)

        top = await db.get_top_pvp_players(2)
        assert len(top) == 2
        assert top[0].username == "player2"
        assert top[0].pvp_wins == 12
        assert top[1].username == "player1"
        assert top[1].pvp_wins == 5

        if os.path.exists(db_path):
            os.remove(db_path)

    asyncio.run(run_test())
