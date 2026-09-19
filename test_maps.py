"""Tests for the board *map* catalog (pure logic, no GUI, no filesystem)."""
from __future__ import annotations

from game import board as board_mod
from game.tile_types import TileType
from game.board import build_board, build_map, _grid, Tile
from game.game import Game, GameOver
from game.player import Player
from game.maps import (
    GameMap,
    by_key,
    available_maps,
)


def _run_players(g, steps=200) -> None:
    g.play(steps)


def test_available_maps_contains_all_five():
    maps = available_maps()
    for key in ("classic", "hongkong", "taiwan", "world", "gpa"):
        assert key in maps


def test_by_key_unknown():
    try:
        by_key("does-not-exist")
    except KeyError:
        return
    assert False, "expected KeyError for unknown map"


def test_by_key_known():
    for key in available_maps():
        gmap = by_key(key)
        assert isinstance(gmap, GameMap)
        assert len(gmap.tiles) == 40


def test_each_map_builds_full_board():
    for key in available_maps():
        b = build_map(by_key(key))
        assert len(b.tiles) == 40
        # grid covers every tile
        assert all(i in b.grid for i in range(40))
        # every tile's category is a real TileType
        for t in b.tiles:
            assert t.category in list(TileType)
        # first tile is always GO
        assert b.tiles[0].category == TileType.GO


def test_each_map_has_all_required_categories():
    for key in available_maps():
        b = build_map(by_key(key))
        categories = {t.category for t in b.tiles}
        for required in (
            TileType.GO,
            TileType.CHANCE,
            TileType.COMMUNITY,
            TileType.TAX,
            TileType.RAILROAD,
            TileType.UTILITY,
            TileType.PROPERTY,
            TileType.JAIL,
            TileType.FREE,
            TileType.GO_JAIL,
        ):
            assert required in categories, f"{key} missing {required.name}"


def test_board_from_build_maps_matches_tile_names():
    """The maps keep their distinct themed tile names."""
    classic = build_map(by_key("classic"))
    assert classic.tile_by_index(0).name == "起点"
    hongkong = build_map(by_key("hongkong"))
    assert hongkong.tile_by_index(1).name == "深水埗"
    assert hongkong.tile_by_index(39).name == "太平山"
    taiwan = build_map(by_key("taiwan"))
    assert taiwan.tile_by_index(0).name == "起点"
    world = build_map(by_key("world"))
    assert world.tile_by_index(0).name == "机场"
    gpa = build_map(by_key("gpa"))
    assert gpa.tile_by_index(0).name == "入学点"


def test_classic_map_is_standard_monopoly_layout():
    """The classic map mirrors the standard 40-tile Monopoly board."""
    b = build_map(by_key("classic"))
    assert len(b.tiles) == 40
    # 8 个地产集团，每组 2-3 块
    groups: dict = {}
    for t in b.tiles:
        if t.category == TileType.PROPERTY:
            groups.setdefault(t.group, []).append(t)
    assert set(groups) == {"brown", "lightblue", "pink", "orange", "red", "yellow", "green", "darkblue"}
    assert all(2 <= len(v) <= 3 for v in groups.values())
    # 铁路 4 / 公用事业 2 / 机会 3 / 社区 3 / 税 2
    assert sum(1 for t in b.tiles if t.category == TileType.RAILROAD) == 4
    assert sum(1 for t in b.tiles if t.category == TileType.UTILITY) == 2
    assert sum(1 for t in b.tiles if t.category == TileType.CHANCE) == 3
    assert sum(1 for t in b.tiles if t.category == TileType.COMMUNITY) == 3
    assert sum(1 for t in b.tiles if t.category == TileType.TAX) == 2
    # 四个角落
    assert b.tiles[0].category == TileType.GO
    assert b.tiles[10].category == TileType.JAIL
    assert b.tiles[20].category == TileType.FREE
    assert b.tiles[30].category == TileType.GO_JAIL
    # 标志性地名
    assert b.tiles[1].name == "地中海大道"
    assert b.tiles[37].name == "公园广场"
    assert b.tiles[39].name == "木板路"


def test_board_from_map_is_valid_for_engine():
    """The engine must be able to run a game on a freshly built map."""
    b = build_map(by_key("world"))
    players = [Player(f"BOT{i+1}", holds=2) for i in range(4)]
    g = Game(players, board=b, seed=7, max_turns=500)
    g.start()
    g.run(60)  # should not raise
