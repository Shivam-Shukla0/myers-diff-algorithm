import sys
from array import array


def myers(old_sequence, new_sequence):
    """Return a minimal edit script for old_sequence -> new_sequence."""

    old_length = len(old_sequence)
    new_length = len(new_sequence)

    # Remove the common prefix.
    prefix_length = 0

    while (
        prefix_length < old_length
        and prefix_length < new_length
        and old_sequence[prefix_length] == new_sequence[prefix_length]
    ):
        prefix_length += 1

    # Remove the common suffix.
    suffix_length = 0

    while (
        suffix_length < old_length - prefix_length
        and suffix_length < new_length - prefix_length
        and old_sequence[old_length - 1 - suffix_length]
        == new_sequence[new_length - 1 - suffix_length]
    ):
        suffix_length += 1

    middle_operations = _myers_core(
        old_sequence[prefix_length:old_length - suffix_length],
        new_sequence[prefix_length:new_length - suffix_length],
    )

    return (
        [" "] * prefix_length
        + middle_operations
        + [" "] * suffix_length
    )


def _myers_core(old_sequence, new_sequence):
    old_length = len(old_sequence)
    new_length = len(new_sequence)

    if old_length == 0:
        return ["+"] * new_length

    if new_length == 0:
        return ["-"] * old_length

    maximum_distance = old_length + new_length
    diagonal_offset = maximum_distance + 1

    frontier = [0] * (2 * maximum_distance + 3)

    # Store the frontier needed for reconstruction.
    history = []

    final_distance = -1

    for distance in range(maximum_distance + 1):

        if distance > 0:
            history.append(
                array(
                    "i",
                    frontier[
                        diagonal_offset - (distance - 1):
                        diagonal_offset + distance:
                        2
                    ],
                )
            )

        for diagonal in range(-distance, distance + 1, 2):

            if (
                diagonal == -distance
                or (
                    diagonal != distance
                    and frontier[diagonal_offset + diagonal - 1]
                    < frontier[diagonal_offset + diagonal + 1]
                )
            ):
                # Move down: insert an element.
                old_position = frontier[
                    diagonal_offset + diagonal + 1
                ]

            else:
                # Move right: delete an element.
                old_position = (
                    frontier[diagonal_offset + diagonal - 1] + 1
                )

            new_position = old_position - diagonal

            # Follow matching elements.
            while (
                old_position < old_length
                and new_position < new_length
                and old_sequence[old_position]
                == new_sequence[new_position]
            ):
                old_position += 1
                new_position += 1

            frontier[diagonal_offset + diagonal] = old_position

            if (
                old_position >= old_length
                and new_position >= new_length
            ):
                final_distance = distance
                break

        if final_distance >= 0:
            break

    operations = []

    old_position = old_length
    new_position = new_length

    # Reconstruct the shortest edit script.
    for distance in range(final_distance, 0, -1):

        saved_frontier = history[distance - 1]
        previous_distance = distance - 1

        diagonal = old_position - new_position

        if (
            diagonal == -distance
            or (
                diagonal != distance
                and saved_frontier[
                    (diagonal - 1 + previous_distance) // 2
                ]
                <
                saved_frontier[
                    (diagonal + 1 + previous_distance) // 2
                ]
            )
        ):
            previous_diagonal = diagonal + 1
            is_insertion = True

        else:
            previous_diagonal = diagonal - 1
            is_insertion = False

        previous_old_position = saved_frontier[
            (previous_diagonal + previous_distance) // 2
        ]

        previous_new_position = (
            previous_old_position - previous_diagonal
        )

        if is_insertion:
            edit_old_position = previous_old_position
            edit_new_position = previous_new_position + 1
        else:
            edit_old_position = previous_old_position + 1
            edit_new_position = previous_new_position

        # Add the matching snake.
        while old_position > edit_old_position:
            operations.append(" ")
            old_position -= 1
            new_position -= 1

        # Add the actual edit.
        if is_insertion:
            operations.append("+")
        else:
            operations.append("-")

        old_position = previous_old_position
        new_position = previous_new_position

    # Remaining matching prefix.
    while old_position > 0:
        operations.append(" ")
        old_position -= 1
        new_position -= 1

    operations.reverse()

    return operations


def read_lines(file_path):
    with open(file_path, "rb") as input_file:
        file_data = input_file.read()

    lines = file_data.split(b"\n")

    if lines and lines[-1] == b"":
        lines.pop()

    return lines


def blocks(operations, old_lines, new_lines):
    """Yield keep records or changed blocks with deletions first."""

    old_index = 0
    new_index = 0

    deletions = []
    insertions = []

    for operation in operations:

        if operation == " ":

            if deletions or insertions:
                yield ("block", deletions, insertions)
                deletions, insertions = [], []

            yield ("keep", old_lines[old_index])

            old_index += 1
            new_index += 1

        elif operation == "-":

            deletions.append(old_lines[old_index])
            old_index += 1

        else:

            insertions.append(new_lines[new_index])
            new_index += 1

    if deletions or insertions:
        yield ("block", deletions, insertions)


def ranges_to_str(ranges):
    if not ranges:
        return "."

    return ",".join(
        "%d-%d" % (start, end)
        for start, end in ranges
    )


def add_range(ranges, position):
    if ranges and ranges[-1][1] == position:
        ranges[-1][1] = position + 1
    else:
        ranges.append([position, position + 1])


def highlight_pair(old_text, new_text):
    old_string = old_text.decode("utf-8")
    new_string = new_text.decode("utf-8")

    operations = myers(old_string, new_string)

    old_position = 0
    new_position = 0

    old_ranges = []
    new_ranges = []

    for operation in operations:

        if operation == " ":
            old_position += 1
            new_position += 1

        elif operation == "-":
            add_range(old_ranges, old_position)
            old_position += 1

        else:
            add_range(new_ranges, new_position)
            new_position += 1

    result = (
        "? "
        + ranges_to_str(old_ranges)
        + " | "
        + ranges_to_str(new_ranges)
    )

    return result.encode()


def main():
    if (
        len(sys.argv) != 4
        or sys.argv[1] not in ("lines", "highlight")
    ):
        sys.stderr.write(
            "usage: main.py lines|highlight A B\n"
        )
        sys.exit(2)

    mode = sys.argv[1]
    old_path = sys.argv[2]
    new_path = sys.argv[3]

    try:
        old_lines = read_lines(old_path)
        new_lines = read_lines(new_path)

    except OSError as error:
        sys.stderr.write(
            "error: %s\n" % error
        )
        sys.exit(2)

    operations = myers(old_lines, new_lines)

    output = []

    for item in blocks(
        operations,
        old_lines,
        new_lines,
    ):

        if item[0] == "keep":
            output.append(
                b" " + item[1] + b"\n"
            )
            continue

        _, deletions, insertions = item

        # Deletions must be printed before insertions.
        for deleted_line in deletions:
            output.append(
                b"-" + deleted_line + b"\n"
            )

        for insertion_index, inserted_line in enumerate(insertions):

            output.append(
                b"+" + inserted_line + b"\n"
            )

            if (
                mode == "highlight"
                and insertion_index < len(deletions)
            ):
                output.append(
                    highlight_pair(
                        deletions[insertion_index],
                        inserted_line,
                    )
                    + b"\n"
                )

    sys.stdout.buffer.write(
        b"".join(output)
    )


if __name__ == "__main__":
    main()