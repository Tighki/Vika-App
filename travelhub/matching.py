"""Подбор гида на заявку.

Балл активного гида:
    * направление совпало с заявкой: +40;
    * универсальный гид: +12;
    * тот же регион: +18;
    * гид с регионом «любой»: +8;
    * средняя оценка × 4, а если оценок нет — нейтральные 4,2 × 4;
    * за каждую заявку в работе снимаются баллы, у высокого приоритета штраф больше;
    * гид с четырьмя и более активными заявками не выбирается, пока есть кто-то ниже предела.
"""

from travelhub import db

THEME_BONUS = 40
UNIVERSAL_BONUS = 12
REGION_BONUS = 18
ANY_REGION_BONUS = 8
RATING_WEIGHT = 4
NEUTRAL_RATING = 4.2
MAX_ACTIVE = 4
LOAD_WEIGHT = {
    "low": 3,
    "normal": 5,
    "high": 9,
}
PRIORITY_RANK = {"high": 0, "normal": 1, "low": 2}


def _rating(guide):
    value = db.guide_rating(guide)
    if value is None:
        return NEUTRAL_RATING
    return value


def score_guide(guide, theme, region, priority, load):
    """Возвращает (score, reasons). Чем больше score, тем лучше кандидат."""
    reasons = []
    score = 0.0

    if guide["specialty"] == theme:
        score += THEME_BONUS
        reasons.append(f"направление совпало +{THEME_BONUS}")
    elif guide["specialty"] == "other":
        score += UNIVERSAL_BONUS
        reasons.append(f"универсальный гид +{UNIVERSAL_BONUS}")
    else:
        reasons.append("направление не совпало")

    if region != "other" and guide["region"] == region:
        score += REGION_BONUS
        reasons.append(f"тот же регион +{REGION_BONUS}")
    elif guide["region"] == "other":
        score += ANY_REGION_BONUS
        reasons.append(f"работает в разных регионах +{ANY_REGION_BONUS}")
    else:
        reasons.append("другой регион")

    rating = _rating(guide)
    rating_points = rating * RATING_WEIGHT
    score += rating_points
    if db.guide_rating(guide) is None:
        reasons.append(f"оценок пока нет, нейтральный балл +{rating_points:.1f}")
    else:
        reasons.append(f"рейтинг {rating:.1f} +{rating_points:.1f}")

    penalty = load * LOAD_WEIGHT.get(priority, 5)
    score -= penalty
    reasons.append(f"загрузка {load} (−{penalty})")
    if load >= MAX_ACTIVE:
        reasons.append(f"предел {MAX_ACTIVE} заявок")
    return score, reasons


def pick_guide(theme, region, priority="normal"):
    """Возвращает (guide, debug) либо (None, debug), если активных гидов нет."""
    guides = db.list_guides(only_active=True)
    under, over = [], []
    for guide in guides:
        load = db.active_load(guide["id"])
        score, reasons = score_guide(guide, theme, region, priority, load)
        item = (score, load, guide, reasons)
        (over if load >= MAX_ACTIVE else under).append(item)

    pool = under or over
    if not pool:
        return None, ["нет активных гидов"]

    pool.sort(key=lambda item: (-item[0], item[1], item[2]["id"]))
    best_score, _load, best, best_reasons = pool[0]
    debug = [f"{guide['full_name']}: {score:.1f}" for score, _load, guide, _reasons in pool]
    summary = f"Назначен {best['full_name']} (оценка {best_score:.1f})"
    if not under:
        summary += f". Все на пределе {MAX_ACTIVE}, выбран с меньшей загрузкой"
    elif over:
        skipped = ", ".join(guide["full_name"] for _score, _load, guide, _reasons in over)
        debug.append(f"Сверх предела {MAX_ACTIVE}: {skipped}")
    debug.insert(0, summary)
    debug[1:1] = best_reasons
    return best, debug


def distribute(request_id, actor_id=None):
    """Назначает гида на одну заявку. Возвращает (guide, debug)."""
    request = db.get_request(request_id)
    if not request:
        return None, ["Заявка не найдена"]
    if request["status"] not in ("new", "assigned"):
        return None, ["Заявка уже закрыта"]
    guide, debug = pick_guide(request["theme"], request["region"], request["priority"])
    if not guide:
        return None, debug
    load = db.active_load(guide["id"])
    _score, reasons = score_guide(guide, request["theme"], request["region"], request["priority"], load)
    ok, message = db.assign_request(request_id, guide["id"], actor_id, note="; ".join(reasons))
    if not ok:
        return None, [message, *debug]
    return guide, debug


def distribute_pending(actor_id=None):
    """Назначает гидов на все новые заявки без гида. Сначала более срочные."""
    pending = [
        request
        for request in db.list_requests()
        if request["guide_id"] is None and request["status"] == "new"
    ]
    pending.sort(key=lambda request: (PRIORITY_RANK.get(request["priority"], 9), request["id"]))
    lines = []
    assigned = 0
    for request in pending:
        guide, _debug = distribute(request["id"], actor_id)
        target = guide["full_name"] if guide else "нет гида"
        lines.append(f"№{request['id']} {request['title']} → {target}")
        if guide:
            assigned += 1
    return assigned, lines
