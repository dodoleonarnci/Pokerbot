"""Reading the tables: split cell -> actor-bucket cell -> plain node -> pooled spot. Never raises."""

USABLE = 20
BET_SIZE_VERDICT = 200


def _sum_cells(cells):
    total = {"n": 0, "a": {}, "cls": {}}
    for cell in cells:
        total["n"] += cell["n"]
        for code, count in cell["a"].items():
            total["a"][code] = total["a"].get(code, 0) + count
        for code, table in cell.get("cls", {}).items():
            mine = total["cls"].setdefault(code, {})
            for cls, count in table.items():
                mine[cls] = mine.get(cls, 0) + count
    return total


def lookup(tree, pool, path, actor, actor_pub=None, opp_pub=None, key=None, usable=USABLE):
    """Returns (level, cell, thin): the first level with `usable` samples, walking back as needed.

    `thin` lists the levels that were passed over, so a reader can say a cell was thin.
    """
    node_key = f"{path} @{actor}" if path else f"@{actor}"
    node = tree.get(node_key)
    thin = []
    if node is not None:
        splits = node.get("splits", {})
        if actor_pub is not None and opp_pub is not None:
            cell = splits.get(f"{actor_pub}|{opp_pub}")
            if cell and cell["n"] >= usable:
                return "split", cell, thin
            thin.append("split")
        if actor_pub is not None:
            prefix = actor_pub + "|"
            cell = _sum_cells(c for k, c in splits.items() if k.startswith(prefix))
            if cell["n"] >= usable:
                return "actor_bucket", cell, thin
            thin.append("actor_bucket")
        if node["n"] >= usable:
            return "node", node, thin
        thin.append("node")
        key = key or node.get("k")
    if key:
        spot = pool.get("spots", {}).get(key)
        if spot:
            return "pool", spot, thin
        thin.append("pool")
    return "empty", {"n": 0, "a": {}, "cls": {}}, thin


def rate(cell, codes=None):
    """Action frequencies of a cell; an empty cell gives an empty dict."""
    counts = cell.get("a", {})
    total = sum(counts.values())
    if not total:
        return {}
    return {code: count / total for code, count in counts.items() if codes is None or code in codes}
