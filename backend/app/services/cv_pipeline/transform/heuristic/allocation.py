def allocate_matches_to_nearest_preceding_anchor(
    matches_with_offsets: list[tuple[str, int]],
    anchor_offsets: list[int],
) -> dict[int, list[str]]:
    """Przypisuje każde dopasowanie (np. technologię) do najbliższego
    wcześniejszego kotwicy (np. zakresu dat stanowiska) na podstawie offsetu
    w tekście. Dopasowanie bez żadnej wcześniejszej kotwicy jest odrzucane.

    Zastępuje krok, w którym LLM decydował, do którego stanowiska należy dana
    technologia (`skills_used`) — tutaj o przypisaniu decyduje wyłącznie
    pozycja tekstu, bez generowania treści.
    """
    anchors_sorted_by_offset = sorted(
        range(len(anchor_offsets)), key=lambda i: anchor_offsets[i]
    )

    result: dict[int, list[str]] = {i: [] for i in range(len(anchor_offsets))}

    for name, offset in matches_with_offsets:
        best_anchor_index: int | None = None
        for anchor_index in anchors_sorted_by_offset:
            if anchor_offsets[anchor_index] <= offset:
                best_anchor_index = anchor_index
            else:
                break

        if best_anchor_index is not None:
            result[best_anchor_index].append(name)

    for anchor_index, names in result.items():
        result[anchor_index] = sorted(set(names))

    return result


def pick_nearest_label_per_anchor(
    labels_with_offsets: list[tuple[str, int]],
    anchor_offsets: list[int],
) -> dict[int, str | None]:
    """Przypisuje każdej kotwicy (np. zakresowi dat stanowiska) etykietę
    (np. tytuł stanowiska) o najmniejszej odległości offsetu w tekście - w
    obie strony, nie tylko wcześniejszą. W CV tytuł stanowiska równie często
    stoi przed datami ("Senior Developer, 2022 - obecnie") jak i po nich
    ("2022 - obecnie, Senior Developer"), więc w przeciwieństwie do
    allocate_matches_to_nearest_preceding_anchor tu liczy się bliskość, a nie
    kierunek w tekście. Każda etykieta i każda kotwica biorą udział w co
    najwyżej jednym przypisaniu (greedy nearest-first matching)."""
    result: dict[int, str | None] = dict.fromkeys(range(len(anchor_offsets)))
    if not labels_with_offsets or not anchor_offsets:
        return result

    candidate_pairs = sorted(
        (
            (abs(anchor_offsets[anchor_index] - label_offset), anchor_index, label_index)
            for label_index, (_label, label_offset) in enumerate(labels_with_offsets)
            for anchor_index in range(len(anchor_offsets))
        ),
        key=lambda pair: pair[0],
    )

    assigned_anchors: set[int] = set()
    assigned_labels: set[int] = set()
    for _distance, anchor_index, label_index in candidate_pairs:
        if anchor_index in assigned_anchors or label_index in assigned_labels:
            continue

        result[anchor_index] = labels_with_offsets[label_index][0]
        assigned_anchors.add(anchor_index)
        assigned_labels.add(label_index)

    return result
