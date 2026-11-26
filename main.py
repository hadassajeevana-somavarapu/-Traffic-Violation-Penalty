# Traffic Violation Penalty Calculator
# Processes multiple traffic violations using vehicle category multipliers,
# offence base fines, repeat-offence status, and demerit points to compute
# total penalties and determine license disqualification conditions.

VEHICLE_MULTIPLIERS = {
    "TWO_WHEELER": 1.0,
    "CAR": 1.25,
    "COMMERCIAL": 1.75,
    "HEAVY_VEHICLE": 2.0,
}

# Predefined offence rules: base_fine, demerit_points, and severe_repeat_disqualify flag
OFFENCE_RULES = {
    "NO_HELMET_SEATBELT": {"base_fine": 1000.0, "points": 2, "severe": False},
    "SIGNAL_JUMP": {"base_fine": 1500.0, "points": 3, "severe": False},
    "OVERSPEEDING": {"base_fine": 2000.0, "points": 4, "severe": True},
    "NO_LICENSE_INSURANCE": {"base_fine": 2500.0, "points": 4, "severe": False},
    "DRUNK_DRIVING": {"base_fine": 10000.0, "points": 8, "severe": True},
    "DANGEROUS_DRIVING": {"base_fine": 5000.0, "points": 6, "severe": True},
}

REPEAT_OFFENCE_SURCHARGE_RATE = 0.50  # +50% fine for a repeat offence
DISQUALIFICATION_POINT_LIMIT = 12     # Disqualified if total demerit points >= 12
DISQUALIFICATION_OFFENCE_LIMIT = 4    # Disqualified if >= 4 violations in a single review


def evaluate_violations(vehicle_category, violations):
    """
    vehicle_category: str key in VEHICLE_MULTIPLIERS
    violations: list of dicts, each with:
        - 'offence': str key in OFFENCE_RULES
        - 'is_repeat': bool
    """
    v_cat = vehicle_category.strip().upper()
    if v_cat not in VEHICLE_MULTIPLIERS:
        raise ValueError(f"Invalid vehicle category '{vehicle_category}'.")

    multiplier = VEHICLE_MULTIPLIERS[v_cat]
    records = []
    total_penalty = 0.0
    total_points = 0
    disqualification_reasons = []

    for idx, item in enumerate(violations, start=1):
        offence_code = item["offence"].strip().upper()
        is_repeat = bool(item["is_repeat"])

        if offence_code not in OFFENCE_RULES:
            raise ValueError(f"Unknown offence type '{offence_code}'.")

        rule = OFFENCE_RULES[offence_code]
        base_fine = rule["base_fine"]
        vehicle_adjusted_fine = base_fine * multiplier
        repeat_surcharge = (
            vehicle_adjusted_fine * REPEAT_OFFENCE_SURCHARGE_RATE if is_repeat else 0.0
        )
        final_item_fine = vehicle_adjusted_fine + repeat_surcharge

        # Repeat offences also add +1 extra demerit point
        points = rule["points"] + (1 if is_repeat else 0)

        total_penalty += final_item_fine
        total_points += points

        if offence_code == "DRUNK_DRIVING" and is_repeat:
            disqualification_reasons.append(
                f"Violation #{idx}: Repeat Drunk Driving offence (mandatory suspension)"
            )
        elif rule["severe"] and is_repeat and v_cat in ("COMMERCIAL", "HEAVY_VEHICLE"):
            disqualification_reasons.append(
                f"Violation #{idx}: Repeat severe offence ({offence_code}) on {v_cat}"
            )

        records.append({
            "index": idx,
            "offence": offence_code,
            "is_repeat": is_repeat,
            "base_fine": base_fine,
            "adjusted_fine": vehicle_adjusted_fine,
            "repeat_surcharge": repeat_surcharge,
            "final_fine": final_item_fine,
            "points": points,
        })

    if total_points >= DISQUALIFICATION_POINT_LIMIT:
        disqualification_reasons.append(
            f"Accumulated {total_points} demerit points (limit: {DISQUALIFICATION_POINT_LIMIT})"
        )

    if len(records) >= DISQUALIFICATION_OFFENCE_LIMIT:
        disqualification_reasons.append(
            f"Recorded {len(records)} violations in one cycle (limit: {DISQUALIFICATION_OFFENCE_LIMIT})"
        )

    # Deduplicate reasons while preserving order
    unique_reasons = list(dict.fromkeys(disqualification_reasons))

    return {
        "vehicle_category": v_cat,
        "vehicle_multiplier": multiplier,
        "records": records,
        "total_penalty": total_penalty,
        "total_points": total_points,
        "is_disqualified": len(unique_reasons) > 0,
        "disqualification_reasons": unique_reasons,
    }


def print_penalty_report(result, currency="INR"):
    print("\n" + "=" * 78)
    print("TRAFFIC VIOLATION PENALTY & LICENSE STATUS REPORT")
    print("=" * 78)
    print(f"Vehicle Category   : {result['vehicle_category']} (Multiplier: {result['vehicle_multiplier']}x)")
    print("-" * 78)
    print(
        f"{'#':<3} | {'Offence':<21} | {'Repeat':<6} | {'Adj. Fine':>10} | "
        f"{'Surcharge':>10} | {'Final Fine':>10} | {'Pts':>3}"
    )
    print("-" * 78)

    for r in result["records"]:
        rep_str = "Yes" if r["is_repeat"] else "No"
        print(
            f"{r['index']:<3} | {r['offence']:<21} | {rep_str:<6} | {r['adjusted_fine']:>10.2f} | "
            f"{r['repeat_surcharge']:>10.2f} | {r['final_fine']:>10.2f} | {r['points']:>3}"
        )

    print("-" * 78)
    print(f"Total Penalty Payable  : {result['total_penalty']:.2f} {currency}")
    print(f"Total Demerit Points   : {result['total_points']} / {DISQUALIFICATION_POINT_LIMIT}")

    if result["is_disqualified"]:
        print("License Status         : DISQUALIFIED / SUSPENDED")
        print("Disqualification Rules Triggered:")
        for reason in result["disqualification_reasons"]:
            print(f"  * {reason}")
    else:
        print("License Status         : ACTIVE (No Disqualification Triggered)")
    print("=" * 78)


def main():
    print("Vehicle Categories:", ", ".join(VEHICLE_MULTIPLIERS.keys()))
    vehicle_category = input("Enter vehicle category: ").strip()

    print("\nAvailable Offence Codes:")
    for code, rule in OFFENCE_RULES.items():
        print(f"  - {code:<21} (Base Fine: {rule['base_fine']:.0f}, Points: {rule['points']})")

    num_violations = int(input("\nEnter number of violations to process: "))
    violations = []

    for i in range(1, num_violations + 1):
        print(f"\nViolation #{i}:")
        offence = input("  Offence code: ").strip()
        repeat_input = input("  Is this a repeat offence? (y/n): ").strip().lower()
        violations.append({
            "offence": offence,
            "is_repeat": repeat_input in ("y", "yes"),
        })

    try:
        result = evaluate_violations(vehicle_category=vehicle_category, violations=violations)
        print_penalty_report(result)
    except ValueError as err:
        print(f"\nInput Error: {err}")


if __name__ == "__main__":
    main()
