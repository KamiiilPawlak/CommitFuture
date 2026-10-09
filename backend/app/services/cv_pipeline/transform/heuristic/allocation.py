def allocate_matches_to_nearest_preceding_anchor(
    matches_with_offsets: list[tuple[str, int]],
    anchor_offsets: list[int],
) -> dict[int, list[str]]:

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
    result: dict[int, str | None] = dict.fromkeys(range(len(anchor_offsets)))
    if not labels_with_offsets or not anchor_offsets:
        return result

    candidate_pairs = sorted(
        (
            (
                abs(anchor_offsets[anchor_index] - label_offset),
                anchor_index,
                label_index,
            )
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
