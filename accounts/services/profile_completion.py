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

    2. PORTFOLIO (20 puncte) - minim 3 poze cu lucrări:
       - 3+ poze: 20p
       - 1-2 poze: proporțional (10p per poză)

    3. SERVICII (10 puncte) - categori în care lucrezi:
       - Minim 1 categorie: 10p

    4. OPȚIONAL (10 puncte) - detalii suplimentare:
       - Ani experiență: 3p
       - Tarife (tarif orar SAU valoare minimă): 3p
       - Rețele sociale (website/facebook/instagram): 2p
       - CUI firmă: 2p

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
        "portfolio": {"score": 0, "max": 20, "items": {}},
        "servicii": {"score": 0, "max": 10, "items": {}},
        "optional": {"score": 0, "max": 10, "items": {}},
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

    # 2. PORTFOLIO (20 puncte) - requires craftsman to be saved
    if craftsman.pk:
        portfolio_count = craftsman.portfolio_images.count()
        if portfolio_count >= 3:
            portfolio_score = 20
            breakdown["portfolio"]["items"]["images"] = {"score": 20, "status": "✓", "count": portfolio_count}
        elif portfolio_count > 0:
            portfolio_score = (portfolio_count * 20) // 3
            breakdown["portfolio"]["items"]["images"] = {
                "score": portfolio_score,
                "status": "⚠",
                "count": portfolio_count,
                "needed": f"Adaugă {3 - portfolio_count} poze pentru 20p"
            }
        else:
            portfolio_score = 0
            breakdown["portfolio"]["items"]["images"] = {"score": 0, "status": "✗", "needed": "Adaugă minim 3 poze cu lucrări"}

        score += portfolio_score
        breakdown["portfolio"]["score"] = portfolio_score
    else:
        breakdown["portfolio"]["items"]["images"] = {"score": 0, "status": "✗", "needed": "Salvează profilul pentru a adăuga poze"}

    # 3. SERVICII (10 puncte)
    if craftsman.pk and hasattr(craftsman, "services") and craftsman.services.exists():
        score += 10
        breakdown["servicii"]["score"] = 10
        breakdown["servicii"]["items"]["categories"] = {"score": 10, "status": "✓"}
    else:
        breakdown["servicii"]["items"]["categories"] = {"score": 0, "status": "✗", "needed": "Adaugă minim 1 categorie de servicii"}

    # 4. OPȚIONAL (10 puncte)
    if craftsman.years_experience:
        score += 3
        breakdown["optional"]["score"] += 3
        breakdown["optional"]["items"]["experience"] = {"score": 3, "status": "✓"}
    else:
        breakdown["optional"]["items"]["experience"] = {"score": 0, "status": "○", "optional": True}

    if craftsman.hourly_rate or craftsman.min_job_value:
        score += 3
        breakdown["optional"]["score"] += 3
        breakdown["optional"]["items"]["pricing"] = {"score": 3, "status": "✓"}
    else:
        breakdown["optional"]["items"]["pricing"] = {"score": 0, "status": "○", "optional": True}

    if craftsman.website_url or craftsman.facebook_url or craftsman.instagram_url:
        score += 2
        breakdown["optional"]["score"] += 2
        breakdown["optional"]["items"]["social"] = {"score": 2, "status": "✓"}
    else:
        breakdown["optional"]["items"]["social"] = {"score": 0, "status": "○", "optional": True}

    if craftsman.company_cui:
        score += 2
        breakdown["optional"]["score"] += 2
        breakdown["optional"]["items"]["company"] = {"score": 2, "status": "✓"}
    else:
        breakdown["optional"]["items"]["company"] = {"score": 0, "status": "○", "optional": True}

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
