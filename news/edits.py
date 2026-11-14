"""The catalogue of edits Claude chooses from, scene by scene (AGENT_JNEWS.md, "Bảng cách edit").

A picture of a story may carry "move": "<name>" (how the picture moves while it is on screen), a scene "cut":
"<name>" (how the scene arrives) and "why" (a short reason in Vietnamese, never drawn in the video). A picture
without "move" and a scene without "cut" keep the automatic choice of before: the four old moves in turn, and the
cut of the frame (cross-fade for "news", page turn for "paper").
"""

# name -> what it looks like (Vietnamese, for the list the owner reads)
MOVES = {
    "push-in": "tiến chậm vào chủ thể",
    "pull-back": "lùi chậm ra, lộ dần khung cảnh",
    "pan-right": "lia ngang từ trái sang phải",
    "pan-left": "lia ngang từ phải sang trái",
    "rise": "lia dọc từ dưới lên",
    "fall": "lia dọc từ trên xuống",
    "close-up": "cận cảnh chi tiết, gần như đứng yên",
    "reveal": "bắt đầu thật gần rồi lùi nhanh ra toàn cảnh",
    "punch-in": "giật nhanh vào chủ thể rồi giữ",
    "hold": "đứng yên",
}
# a picture shown whole ("fit": "contain": documents, charts, portraits) can only grow, shrink or stay still
CONTAIN_MOVES = ("push-in", "pull-back", "hold")
CUTS = {
    "fade": "mờ chồng sang cảnh mới",
    "page": "lật trang",
    "hard": "cắt thẳng",
    "dip": "tối dần rồi sáng lại",
}
AUTO_MOVES = ("push-in", "pan-right", "pull-back", "pan-left")   # what the automatic choice looks like, in turn
AUTO_CUT = {"news": "fade", "paper": "page"}


def move_problems(photo, where):
    """Problems of the "move" of one picture entry (a dict)."""
    move = photo.get("move")
    if move is None:
        return []
    if move not in MOVES:
        return [f'{where}: unknown "move" {move!r}; choose one of: {", ".join(MOVES)}']
    if photo.get("fit") == "contain" and move not in CONTAIN_MOVES:
        return [f'{where}: "move" {move!r} does not work on a picture shown whole ("fit": "contain"); '
                f'choose one of: {", ".join(CONTAIN_MOVES)}']
    return []


def cut_problems(scene, where):
    problems = []
    cut = scene.get("cut")
    if cut is not None and cut not in CUTS:
        problems.append(f'{where}: unknown "cut" {cut!r}; choose one of: {", ".join(CUTS)}')
    why = scene.get("why")
    if why is not None and (not isinstance(why, str) or not why.strip()):
        problems.append(f'{where}: "why" must be a short sentence, got {why!r}')
    return problems


def edit_list(beats, photos, style):
    """One line per scene for the owner: its headline, the move of each picture, the cut and the reason."""
    lines = []
    for index, beat in enumerate(beats):
        parts = [f"Cảnh {index + 1} · {' '.join(beat.headline.split())}"]
        scene_photos = photos.get(index) or []
        if not scene_photos:
            parts.append("thẻ chữ, không có ảnh")
        for number, photo in enumerate(scene_photos):
            move = photo.move or AUTO_MOVES[(index + number) % len(AUTO_MOVES)]
            if photo.fit == "contain" and not photo.move:
                move = "push-in" if move in ("push-in", "pan-right") else "pull-back"
            parts.append(f"ảnh {number + 1}: {move}" + ("" if photo.move else " (tự động)")
                         + (", hiện cả ảnh" if photo.fit == "contain" else ""))
        if index:
            parts.append(f"vào cảnh: {beat.cut or AUTO_CUT[style] + ' (tự động)'}")
        if beat.why:
            parts.append(f"vì: {beat.why}")
        lines.append(" · ".join(parts))
    return lines
