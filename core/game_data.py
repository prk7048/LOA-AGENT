# core/game_data.py

# 1. 레이드 정보 (주신 데이터 그대로)
RAID_INFO = [
    # --- [종막 카제로스] ---
    {"name": "종막: 카제로스", "difficulty": "하드", "item_level": 1730, "combat_power": 3400, "gold": 52000, "is_single": False},
    {"name": "종막: 카제로스", "difficulty": "노말", "item_level": 1710, "combat_power": 2100, "gold": 40000, "is_single": False},

    # --- [4막 아르모체] ---
    {"name": "4막: 아르모체", "difficulty": "하드", "item_level": 1720, "combat_power": 2600, "gold": 42000, "is_single": False},
    {"name": "4막: 아르모체", "difficulty": "노말", "item_level": 1700, "combat_power": 1800, "gold": 33000, "is_single": False},

    # --- [3막 모르둠] ---
    {"name": "3막: 모르둠", "difficulty": "하드", "item_level": 1700, "combat_power": 2000, "gold": 27000, "is_single": False},
    {"name": "3막: 모르둠", "difficulty": "노말", "item_level": 1680, "combat_power": 0, "gold": 21000, "is_single": True},

    # --- [2막 아브렐슈드] ---
    {"name": "2막: 아브렐슈드", "difficulty": "하드", "item_level": 1690, "combat_power": 1700, "gold": 23000, "is_single": False},
    {"name": "2막: 아브렐슈드", "difficulty": "노말", "item_level": 1670, "combat_power": 0, "gold": 16500, "is_single": True},

    # --- [1막 에기르] ---
    {"name": "1막: 에기르", "difficulty": "하드", "item_level": 1680, "combat_power": 1400, "gold": 18000, "is_single": False},
    {"name": "1막: 에기르", "difficulty": "노말", "item_level": 1660, "combat_power": 0, "gold": 11500, "is_single": True},

    # --- [베히모스] ---
    {"name": "베히모스", "difficulty": "노말", "item_level": 1640, "combat_power": 0, "gold": 7200, "is_single": False},

    # --- [서막 에키드나] ---
    {"name": "서막: 에키드나", "difficulty": "하드", "item_level": 1630, "combat_power": 0, "gold": 7200, "is_single": False},
    {"name": "서막: 에키드나", "difficulty": "노말", "item_level": 1620, "combat_power": 0, "gold": 5500, "is_single": False},
]

# 2. 핵심 알고리즘: Top 3 뽑기
def calculate_best_raids(item_lv, combat_power):
    """
    캐릭터 스펙에 맞는 상위 3개 레이드를 추천합니다.
    - 조건 1: 입장 레벨 & 전투력 충족
    - 조건 2: 같은 레이드면 상위 난이도 1개만 선택 (Lockout 공유)
    - 조건 3: 골드 보상 내림차순 정렬 -> 상위 3개
    """
    
    # A. 입장 가능한 레이드 필터링
    available = []
    for r in RAID_INFO:
        # 전투력이 0인 데이터는 조건 무시(None) 처리하거나 그냥 비교
        req_cp = r.get("combat_power", 0)
        if item_lv >= r["item_level"] and combat_power >= req_cp:
            available.append(r)
            
    # B. 같은 레이드 중 최고 보상만 남기기 (Group By Name)
    # 예: 에키드나 하드, 노말 둘 다 가능하면 -> 하드만 남김
    best_versions = {}
    for r in available:
        name = r["name"]
        if name not in best_versions:
            best_versions[name] = r
        else:
            # 이미 저장된 것보다 지금 것이 골드가 더 많으면 교체
            if r["gold"] > best_versions[name]["gold"]:
                best_versions[name] = r
                
    # 딕셔너리를 다시 리스트로 변환
    final_candidates = list(best_versions.values())
    
    # C. 골드 순으로 정렬 (내림차순)
    final_candidates.sort(key=lambda x: x["gold"], reverse=True)
    
    # D. 상위 3개만 리턴
    return final_candidates[:3]