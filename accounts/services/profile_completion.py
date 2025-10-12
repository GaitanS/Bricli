"""
Service for calculating profile completion percentage for craftsman profiles.
Clear, transparent logic that tells craftsmen exactly what they need to do to reach 100%.
"""


def calculate_profile_completion(craftsman):
    """
    Calculate profile completion percentage (0-100%) for a craftsman profile.

    SCORING BREAKDOWN (100 points total):

    1. OBLIGATORIU (60 puncte) - fără astea nu poți licita:
       - Nume afișat: 10p
       - Locație (județ + oraș): 10p
       - Rază acoperire (5-150 km): 10p
       - Bio (minim 200 caractere): 15p
       - Poză de profil: 15p

    2. PORTFOLIO (40 puncte) - minim 3 poze cu lucrări:
       - 3+ poze: 40p
       - 1-2 poze: proporțional

    3. SERVICII (20 puncte) - categori în care lucrezi:
       - Minim 1 categorie: 20p

    NOTA: Câmpurile opționale (ani experiență, tarife, CUI, rețele sociale) NU mai contează
    pentru procentul de completare. Profilul este 100% complet cu: obligatoriu + portfolio + servicii.

    Args:
        craftsman: CraftsmanProfile instance

    Returns:
        dict with keys:
            - score: int (0-100)
            - is_complete: bool (score == 100)
            - breakdown: dict with detailed scoring
    """
    score = 0
    breakdown = {
        "obligatoriu": {"score": 0, "max": 60, "items": {}},
        "portfolio": {"score": 0, "max": 40, "items": {}},
        "servicii": {"score": 0, "max": 20, "items": {}},
    }

    # 1. OBLIGATORIU (60 puncte)
    if craftsman.display_name:
        score += 10
        breakdown["obligatoriu"]["score"] += 10
        breakdown["obligatoriu"]["items"]["display_name"] = {"score": 10, "status": "✓"}
    else:
        breakdown["obligatoriu"]["items"]["display_name"] = {"score": 0, "status": "✗", "needed": "Adaugă nume afișat"}

    if craftsman.county and craftsman.city:
        score += 10
        breakdown["obligatoriu"]["score"] += 10
        breakdown["obligatoriu"]["items"]["location"] = {"score": 10, "status": "✓"}
    else:
        breakdown["obligatoriu"]["items"]["location"] = {"score": 0, "status": "✗", "needed": "Selectează județ și oraș"}

    if craftsman.coverage_radius_km and 5 <= craftsman.coverage_radius_km <= 150:
        score += 10
        breakdown["obligatoriu"]["score"] += 10
        breakdown["obligatoriu"]["items"]["coverage"] = {"score": 10, "status": "✓"}
    else:
        breakdown["obligatoriu"]["items"]["coverage"] = {"score": 0, "status": "✗", "needed": "Setează rază acoperire (5-150 km)"}

    if craftsman.bio and len(craftsman.bio.strip()) >= 200:
        score += 15
        breakdown["obligatoriu"]["score"] += 15
        breakdown["obligatoriu"]["items"]["bio"] = {"score": 15, "status": "✓"}
    else:
        char_count = len(craftsman.bio.strip()) if craftsman.bio else 0
        breakdown["obligatoriu"]["items"]["bio"] = {
            "score": 0,
            "status": "✗",
            "needed": f"Adaugă bio (minim 200 caractere, ai {char_count})"
        }

    if craftsman.profile_photo:
        score += 15
        breakdown["obligatoriu"]["score"] += 15
        breakdown["obligatoriu"]["items"]["photo"] = {"score": 15, "status": "✓"}
    else:
        breakdown["obligatoriu"]["items"]["photo"] = {"score": 0, "status": "✗", "needed": "Încarcă poză de profil"}

    # 2. PORTFOLIO (40 puncte) - requires craftsman to be saved
    if craftsman.pk:
        portfolio_count = craftsman.portfolio_images.count()
        if portfolio_count >= 3:
            portfolio_score = 40
            breakdown["portfolio"]["items"]["images"] = {"score": 40, "status": "✓", "count": portfolio_count}
        elif portfolio_count > 0:
            portfolio_score = (portfolio_count * 40) // 3
            breakdown["portfolio"]["items"]["images"] = {
                "score": portfolio_score,
                "status": "⚠",
                "count": portfolio_count,
                "needed": f"Adaugă {3 - portfolio_count} poze pentru 40p"
            }
        else:
            portfolio_score = 0
            breakdown["portfolio"]["items"]["images"] = {"score": 0, "status": "✗", "needed": "Adaugă minim 3 poze cu lucrări"}

        score += portfolio_score
        breakdown["portfolio"]["score"] = portfolio_score
    else:
        breakdown["portfolio"]["items"]["images"] = {"score": 0, "status": "✗", "needed": "Salvează profilul pentru a adăuga poze"}

    # 3. SERVICII (20 puncte)
    if craftsman.pk and hasattr(craftsman, "services") and craftsman.services.exists():
        score += 20
        breakdown["servicii"]["score"] = 20
        breakdown["servicii"]["items"]["categories"] = {"score": 20, "status": "✓"}
    else:
        breakdown["servicii"]["items"]["categories"] = {"score": 0, "status": "✗", "needed": "Adaugă minim 1 categorie de servicii"}

    return {
        "score": min(score, 100),
        "is_complete": score >= 100,
        "breakdown": breakdown,
    }


def get_completion_summary(craftsman):
    """
    Get a human-readable summary of what's missing to reach 100%.

    Returns:
        list of strings describing missing requirements
    """
    result = calculate_profile_completion(craftsman)
    missing = []

    # Check obligatoriu items
    for key, item in result["breakdown"]["obligatoriu"]["items"].items():
        if item["status"] == "✗" and "needed" in item:
            missing.append(item["needed"])

    # Check portfolio
    for key, item in result["breakdown"]["portfolio"]["items"].items():
        if item["status"] in ["✗", "⚠"] and "needed" in item:
            missing.append(item["needed"])

    # Check servicii
    for key, item in result["breakdown"]["servicii"]["items"].items():
        if item["status"] == "✗" and "needed" in item:
            missing.append(item["needed"])

    return missing
