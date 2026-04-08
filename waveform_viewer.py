# def parse_vcd(file_path):
#     symbol_map = {}
#     signals = {}
#     current_time = 0
#     in_dumpvars = False

#     with open(file_path, "r") as f:
#         for line in f:
#             line = line.strip()

#             if line.startswith("$var"):
#                 parts = line.split()
#                 symbol = parts[3]
#                 name = parts[4]

#                 symbol_map[symbol] = name
#                 signals[name] = []

#             elif line.startswith("$dumpvars"):
#                 in_dumpvars = True

#             elif line.startswith("$end") and in_dumpvars:
#                 in_dumpvars = False

#             elif line.startswith("#"):
#                 current_time = int(line[1:])

#             # 🔥 HANDLE MULTI-BIT VALUES PROPERLY
#             elif line.startswith("b"):
#                 parts = line.split()
#                 binary_value = parts[0][1:]
#                 symbol = parts[1]

#                 if symbol in symbol_map:
#                     name = symbol_map[symbol]

#                     # ✅ convert full binary → decimal
#                     value = int(binary_value, 2)
#                     signals[name].append((current_time, value))

#             # Single bit
#             elif line and (line[0] in ['0', '1']):
#                 value = int(line[0])
#                 symbol = line[1:]

#                 if symbol in symbol_map:
#                     name = symbol_map[symbol]
#                     signals[name].append((current_time, value))

#     return signals

def parse_vcd(file_path):
    symbol_map = {}
    signals = {}
    current_time = 0
    in_dumpvars = False

    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()

            # ==========================
            # Map symbols
            # ==========================
            if line.startswith("$var"):
                parts = line.split()
                symbol = parts[3]
                name = parts[4]

                symbol_map[symbol] = name
                signals[name] = []

            # ==========================
            # Dumpvars start
            # ==========================
            elif line.startswith("$dumpvars"):
                in_dumpvars = True

            elif line.startswith("$end") and in_dumpvars:
                in_dumpvars = False

            # ==========================
            # Time update
            # ==========================
            elif line.startswith("#"):
                current_time = int(line[1:])

            # ==========================
            # Multi-bit values
            # ==========================
            elif line.startswith("b"):
                parts = line.split()
                binary_value = parts[0][1:]
                symbol = parts[1]

                if symbol in symbol_map:
                    name = symbol_map[symbol]

                    # 🔥 FIX: handle x/z values
                    clean_value = binary_value.replace('x', '0').replace('z', '0')

                    try:
                        value = int(clean_value, 2)
                    except:
                        value = 0

                    signals[name].append((current_time, value))

            # ==========================
            # Single-bit values
            # ==========================
            elif line and (line[0] in ['0', '1']):
                value = int(line[0])
                symbol = line[1:]

                if symbol in symbol_map:
                    name = symbol_map[symbol]
                    signals[name].append((current_time, value))

    # ==========================
    # SAFETY FIX (IMPORTANT)
    # ==========================
    for name in signals:
        if not signals[name]:
            signals[name].append((0, 0))

    return signals