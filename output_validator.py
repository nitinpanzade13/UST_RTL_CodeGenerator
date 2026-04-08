# ==============================
# 1. Generate Truth Table
# ==============================
def generate_truth_table(inputs, logic_type="AND"):
    table = []

    # ==========================
    # ADDER (SPECIAL CASE)
    # ==========================
    if logic_type == "ADDER":
        # 4-bit A + 4-bit B + 1-bit Cin = 9 bits
        for i in range(2**9):
            bits = list(map(int, format(i, "09b")))

            A = bits[:4]
            B = bits[4:8]
            Cin = bits[8]

            A_int = int("".join(map(str, A)), 2)
            B_int = int("".join(map(str, B)), 2)

            total = A_int + B_int + Cin

            Sum = list(map(int, format(total & 0b1111, "04b")))
            Cout = (total >> 4) & 1

            table.append((bits, Sum + [Cout]))

        return table

    # ==========================
    # BASIC LOGIC GATES
    # ==========================
    n = len(inputs)

    for i in range(2**n):
        bits = list(map(int, format(i, f'0{n}b')))

        if logic_type == "AND":
            output = int(all(bits))
            table.append((bits, [output]))

        elif logic_type == "OR":
            output = int(any(bits))
            table.append((bits, [output]))

        elif logic_type == "XOR":
            output = bits[0] ^ bits[1]
            table.append((bits, [output]))

        else:
            table.append((bits, [0]))

    return table


# ==============================
# 2. Parse Simulation Output
# ==============================
def parse_simulation_output(sim_output):
    lines = sim_output.strip().split("\n")
    parsed = []

    for line in lines:
        if "RESULT" in line or line.strip() == "":
            continue

        parts = line.strip().split()

        try:
            values = [int(x, 2) for x in parts]
            parsed.append(values)
        except:
            continue

    return parsed


# ==============================
# 3. Validate Output (🔥 FIXED)
# ==============================
def validate_output(sim_output, truth_table, logic_type="AND"):
    parsed_lines = parse_simulation_output(sim_output)

    correct = 0
    total = min(len(parsed_lines), len(truth_table))

    for sim, (expected_inputs, expected_outputs) in zip(parsed_lines, truth_table):

        # ==========================
        # 🔥 FIX: HANDLE ADDER FORMAT
        # ==========================
        if logic_type == "ADDER":
            # sim format:
            # [A_decimal, B_decimal, Cin, S_decimal, Cout]

            try:
                # Convert A → 4-bit binary list
                A_bits = list(map(int, format(sim[0], "04b")))

                # Convert B → 4-bit
                B_bits = list(map(int, format(sim[1], "04b")))

                # Cin
                Cin_bit = [sim[2]]

                # Combine inputs
                sim_inputs = A_bits + B_bits + Cin_bit

                # Outputs
                S_bits = list(map(int, format(sim[3], "04b")))
                Cout_bit = [sim[4]]

                sim_outputs = S_bits + Cout_bit

            except:
                continue

        else:
            sim_inputs = sim[:len(expected_inputs)]
            sim_outputs = sim[len(expected_inputs):]

        # ==========================
        # Compare outputs ONLY
        # ==========================
        if sim_outputs == expected_outputs:
            correct += 1

    accuracy = correct / total if total > 0 else 0

    return {
        "accuracy": accuracy,
        "passed": correct == total,
        "correct_cases": correct,
        "total_cases": total
    }