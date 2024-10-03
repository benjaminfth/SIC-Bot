def decimal_to_hex(decimal):
    return hex(decimal)[2:].upper()

def pass1(input_text, optab_text):
    saved_labels = []
    input_lines = input_text.strip().splitlines()
    optab_lines = optab_text.strip().splitlines()
    symtab_output = []
    intermediate_output = []
    starting_address = 0
    location_counter = 0
    program_name = ""
    for line in input_lines:
        parts = line.strip().split()
        if len(parts) < 3:
            continue
        label, opcode, operand = parts[0], parts[1], parts[2]
        if opcode == "START":
            program_name = label
            starting_address = int(operand, 16)
            location_counter = starting_address
            intermediate_output.append(f"-\t{label}\t{opcode}\t{operand}")
            continue
        if opcode == "END":
            break
        if label != "-":
            if label in saved_labels:
                return f"Error! Duplicate label: {label} found", None
            saved_labels.append(label)
            symtab_output.append(f"{label}\t{decimal_to_hex(location_counter)}")
        opcode_found = False
        for optab_line in optab_lines:
            optab_opcode, machine_code = optab_line.strip().split()
            if optab_opcode == opcode:
                opcode_found = True
                break
        intermediate_output.append(f"{decimal_to_hex(location_counter)}\t{label}\t{opcode}\t{operand}")
        if opcode_found:
            location_counter += 3
        elif opcode == "BYTE":
            location_counter += len(operand) - 3
        elif opcode == "RESB":
            location_counter += int(operand)
        elif opcode == "WORD":
            location_counter += 3
        elif opcode == "RESW":
            location_counter += 3 * int(operand)
        else:
            return "Error! Invalid opcode", None
    return symtab_output, intermediate_output, program_name, starting_address

def pass2(intermediate_text, symtab_output, optab_text, program_name, starting_address):
    intermediate_lines = intermediate_text.strip().splitlines()
    optab_lines = optab_text.strip().splitlines()
    symtab = {}
    object_output = []
    output_text = []
    for line in symtab_output:
        label, address = line.strip().split()
        symtab[label] = address
    optab = {}
    for line in optab_lines:
        opcode, machine_code = line.strip().split()
        optab[opcode] = machine_code
    loc, label, opcode, operand = intermediate_lines[0].strip().split()
    start = starting_address
    count = 0
    for line in intermediate_lines:
        parts = line.strip().split()
        if len(parts) < 4:
            continue
        loc, label, opcode, operand = parts[0], parts[1], parts[2], parts[3]
        if opcode == "BYTE":
            count += len(operand) - 3
        if opcode not in ["START", "END", "RESW", "RESB", "BYTE"]:
            count += 3
    # Convert the final location counter value from hexadecimal to decimal
    end = int(loc, 16)
    length = end - start
    object_output.append(f"H^{program_name}^00{decimal_to_hex(start)}^{decimal_to_hex(length).zfill(6)}")
    object_output.append(f"T^00{decimal_to_hex(start)}^{decimal_to_hex(count)}^")
    for line in intermediate_lines:
        parts = line.strip().split()
        if len(parts) < 4:
            continue
        loc, label, opcode, operand = parts[0], parts[1], parts[2], parts[3]
        obj_code = ""
        if opcode in ["START", "END", "RESW", "RESB"]:
            output_text.append(f"{loc}\t{label}\t{opcode}\t{operand}")
            continue
        if opcode in optab:
            obj_code = optab[opcode]
            if operand in symtab:
                obj_code += symtab[operand]
            else:
                obj_code += "0000"
        elif opcode == "WORD":
            obj_code = f"{int(operand):06X}"
        elif opcode == "BYTE":
            for char in operand[2:-1]:
                obj_code += f"{decimal_to_hex(ord(char))}"
        object_output[-1] += f"^{obj_code}"
        output_text.append(f"{loc}\t{label}\t{opcode}\t{operand}\t{obj_code}")
    if object_output:
        object_output[-1] = object_output[-1].rstrip('^')
    object_output.append(f"E^00{decimal_to_hex(start)}\n")
    return "\n".join(object_output), "\n".join(output_text)

def assemble(input_text, optab_text):
    symtab_output, intermediate_output, program_name, starting_address = pass1(input_text, optab_text)
    if symtab_output is None:
        return intermediate_output, None, None, None
    intermediate_text = "\n".join(intermediate_output)
    object_output, output_text = pass2(intermediate_text, symtab_output, optab_text, program_name, starting_address)
    return "\n".join(intermediate_output), "\n".join(symtab_output), output_text, object_output