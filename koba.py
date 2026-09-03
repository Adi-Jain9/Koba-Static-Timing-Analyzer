import sys



def read_file(filename):
    '''
    Opens a text file and returns all of its contents as one string

    Input:
        filename: the name or path of the file

    Output:
        The complete contents of the file as a string
    '''
    try:
        file = open(filename, "r")
        text = file.read()
        file.close()
        return text
    except OSError:
        print("Error: could not open", filename)
        sys.exit(1)


def remove_comments(text):
    '''
    Removes block comments and single-line comments from file text

    Input:
        text: the conetents of a verilog or liberty file

    Output:
        A new string containing the original text without comments
    '''
    result = ""
    position = 0

    while position  < len(text):

        # check for beginning of a block comment
        if text[position:position + 2] == "/*":
            end = text.find("*/", position + 2)

            if end == -1:
                break
            # skip everything through the closing */.
            position = end + 2
        
        # check for the beginnning for a single-line comment 
        elif text[position:position + 2] == "//":
            end = text.find("\n", position + 2)

            if end == -1:
                break
            
            # continue from new linme afrer the comment
            position = end

        else:
            result += text[position]
            position += 1

    return result


def find_matching_brace(text, opening_position):
    '''
    Finds the closing brace that matches a specific opening brace

    The function tracks nesting depth so that that the function doesn't stop early

    Input:
        text: the text being searched
        opening_position: The location of the opening brace

    Output:
        The position of the matching closing brace
    '''
    depth = 0
    position = opening_position

    while position < len(text):
        if text[position] == "{":
            depth += 1

        elif text[position] == "}":
            depth -= 1
            
            # depth zero means the original brace was closed
            if depth == 0:
                return position

        position += 1

    return -1


def find_matching_parenthesis(text, opening_position):
    '''
    Finds the closing parenthesis that matches a specific opening parenthesis

    Nested parenthesis are handled by looking at the current depth

    Input:
        text: The text being searched
        opening_parenthesis: the location of the opening parenthesis

    Output:
        The position of the matching closing parenthesis
    '''
    depth = 0
    position = opening_position

    while position < len(text):
        if text[position] == "(":
            depth += 1

        elif text[position] == ")":
            depth -= 1

            if depth == 0:
                return position

        position += 1

    return -1


def remove_quotes(value):
    '''
    Removes surrounding quotation marks and extra whitespace from a value

    Example:
        ' "1ps" ' becomes '1ps'

    Input:
        value: The string that needs to be cleaned

    Output:
        the cleaned string
    '''
    value = value.strip()

    if(
            len(value) >= 2
            and value[0] == '"'
            and value[-1] == '"'
            ):
        return value[1:-1]

    return value


def get_attribute(block, attribute_name):
    '''
    Finds a Liberty attribute insaide a text block and return its value

    Example Liberty attribute:
        direction: input;

    Calling:
        get_attribute(block, "direction")

    returns:
        "input"

    Input:
        block: The liberty block to search
        attribute_name: The exact name of the attribute

    Output:
        The attribute value
    '''
    position = 0

    while True:
        position = block.find(attribute_name, position)

        if position == -1:
            return ""
        # make sure the match is not part of a longer word
        before_ok = (
                position == 0
                or not (
                    block[position - 1].isalnum()
                    or block[position - 1] == "_"
                    )
                )

        after_position = position + len(attribute_name)

        after_ok = (
                after_position >= len(block)
                or not (
                    block[after_position].isalnum()
                    or block[after_position] == "_"
                    )
                )

        if before_ok and after_ok:
            colon = block.find(":", after_position)

            if colon == -1:
                return ""

            semicolon = block.find(";", colon)

            if semicolon == -1:
                return ""
            # the value is everything between the colon and semicolon
            value = block[colon + 1:semicolon].strip()
            return remove_quotes(value)
        
        #the match was part of another word so keep looking
        position += len(attribute_name)


def get_group_name(header, group_type):
    '''
    Gets the name inside the parentheses of a named Liberty group

    Example:
        cell(INV_X1)

    Calling:
        get_group_name(header, "cell")

    returns:
        "INV_X1"

    Input:
        header: the text containing the group header
        group_type: the group type, such as "cell" or "pin"

    Output:
        the group name
    '''
    target = group_type + "("
    start = header.find(target)

    if start == -1:
        return ""
    
    # move to the first character inside the parentheses
    start += len(target)
    end = header.find(")", start)

    if end == -1:
        return ""

    return header[start:end].strip()


def extract_named_blocks(text, group_type):
    '''
    Gets every named Liberty block of a requested type.

    Examples of named blocks:
        cell(INV_X1) { ... }
        pin(A) {...}

    Input:
        text: the liberty file to search
        group_type: the group_type such as "cell" or "pin"

    Output:
        A list of dictionaries. Each dictionary contains:
            name: the name inside the parentheses
            body: the text inside the braces
    '''
    blocks = []
    target = group_type + "("
    position = 0

    while True:
        start = text.find(target, position)

        if start == -1:
            break

        opening_brace = text.find("{", start)

        if opening_brace == -1:
            break
        # brace matching is necessary because groups can contain other groups
        closing_brace = find_matching_brace(text, opening_brace)

        if closing_brace == -1:
            print("Error: unmatched brace in", group_type)
            sys.exit(1)

        header = text[start:opening_brace]
        name = get_group_name(header, group_type)

        body = text[opening_brace + 1: closing_brace]

        blocks.append({"name" : name, "body": body})

        position = closing_brace + 1

    return blocks


def extract_anonymous_blocks(text, group_type):
    '''
    Gets every unnamed Liberty block of a requested type

    Example:
        timing() {...}

    A timing block is anonymous cause nothing in the parentheses

    Input:
        text: the liberty text to search
        group_type: the group type such as "timing"

    Output:
        a list containing the body text from each matching block
    '''
    blocks = []
    target = group_type + "()"
    position = 0

    while True:
        start = text.find(target, position)

        if start == -1:
            break

        opening_brace = text.find("{", start)

        if opening_brace == -1:
            break

        closing_brace = find_matching_brace(text, opening_brace)

        if closing_brace == -1:
            print("Error: unmatched brace in", group_type)
            sys.exit(1)

        body = text[opening_brace + 1: closing_brace]

        blocks.append(body)
        position = closing_brace + 1

    return blocks


def parse_numbers(text):
    '''
    Finds numerical values insaide text and converts them into floats

    Example:
        parse_numbers('"20, 40"')

    returns:
        [20.0, 40.0]

    Input:
        text: Text containing numerical values

    Output:
        a list of floating_point numbers
    '''
    numbers = []
    current = ""

    # build number character by character
    for character in text:
        if(character.isdigit() or character == "."
           or character == "-" or character == "+"
           or character == "e" or character == "E"
           ):
            current += character

        else:
            # a serperator means the current number has ended
            if current != "":
                try:
                    numbers.append(float(current))
                except ValueError:
                    pass

                current = ""

    # store the final number if the text ended immediately after it
    if current != "":
        try:
            numbers.append(float(current))
        except ValueError:
            pass

    return numbers


def parse_table(block, table_name):
    '''
    Reads one 2x2 timing table from a Liberty timing block

    Possible table anmes include:
        cell_rise
        cell_fall
        rise_constraint
        fall_constraint

    Input:
        block: the liberty timing block
        table_name: the name of the table to find

    Output:
        A neste dlist containign two rows and columns

    Example:
        
        [
            [50.0, 100.0],
            [75.0, 200.0]
        ]
    '''
    target = table_name + "("
    start = block.find(target)

    if start == -1:
        return []

    opening_brace = block.find("{", start)

    if opening_brace == -1:
        return []

    closing_brace = find_matching_brace(block, opening_brace)

    if closing_brace == -1:
        return []

    table_body = block[opening_brace + 1:closing_brace]
    
    # timing-table numbers are stored inside values(...)
    values_start = table_body.find("values(")

    if values_start == -1:
        return []

    opening_parenthesis = table_body.find("(", values_start)

    closing_parenthesis = find_matching_parenthesis(table_body, opening_parenthesis)

    if closing_parenthesis == -1:
        return []

    numbers = parse_numbers(table_body[opening_parenthesis + 1: closing_parenthesis])

    # this project expects every timing table to contain 4 values
    if len(numbers) != 4:
        print("Error:", table_name, "must contain four values")
        sys.exit(1)

    #make the flat list into a 2x2 table
    return [[numbers[0], numbers [1]], [numbers[2], numbers[3]]]


def parse_template(liberty_text, template_name):
    '''
    Reads index_1 and index_2 from a Liberty lookup-table template

    Example:
        lu_table_templlate(delay_2x2) {
            index_1("20, 40");
            index_2("5, 30");
        }
    
    Input:
        liberty_text: the complete liberty file
        template_name: the name of the requested template

    Output:
        A dictionary contatining the two index lists

        {
            "index_1": [20.0, 40.0],
            "index_2": [5.0, 30.0]
        }
    '''

    result = {"index_1" : [], "index_2" : []}
    target = ("lu_table_template(" + template_name + ")")

    start = liberty_text.find(target)

    if start == -1:
        return result

    opening_brace = liberty_text.find("{", start)

    if opening_brace == -1:
        return result

    closing_brace = find_matching_brace(liberty_text, opening_brace)

    if closing_brace == -1:
        return result

    body = liberty_text[opening_brace + 1:closing_brace]

    # read index_1
    index_1_start = body.find("index_1(")

    if index_1_start != -1:
        opening = body.find("(", index_1_start)
        closing = find_matching_parenthesis(body, opening)

        if closing != -1:
            result["index_1"] = parse_numbers(body[opening + 1:closing])

    # read index_2
    index_2_start = body.find("index_2(")

    if index_2_start != -1:
        opening = body.find("(", index_2_start)

        closing = find_matching_parenthesis(body, opening)

        if closing != -1:
            result["index_2"] = parse_numbers(body[opening + 1:closing])
    return result


def parse_liberty(filename):
    '''
    Parses a Liberty file and creates a nested library dictionary

    The returned dictionary stores:
        1. The time unit
        2. The delay lookup-table template
        3. The contraint look-up table template
        4. Every library cell
        5. Every pin direction and capacitance
        6. Every timing arc and timing table

    Input:
        filename: the name or path of the Liberty file

    Output:
        a dictionary representing the complete cell library
    '''
    text = remove_comments(read_file(filename))

    # create the top-level library dictionary
    library = {
            "time_unit" : get_attribute(text, "time_unit"),
            "delay_template" : parse_template(text, "delay_2x2"),
            "constraint_template" : parse_template(text, "constraint_2x2"),
            "cells" : {}
            }

    # find every cell(...) block
    cell_blocks = extract_named_blocks(text, "cell")

    for cell_block in cell_blocks:
        cell_name = cell_block["name"]
        cell_body = cell_block["body"]

        # a cell containing ff(...) is a sequential cell
        cell = {
                "sequential" : "ff(" in cell_body, "pins" : {}
                }
        
        # find every pin inside the current cell
        pin_blocks = extract_named_blocks(cell_body, "pin")

        for pin_block in pin_blocks:
            pin_name = pin_block["name"]
            pin_body = pin_block["body"]

            capacitance_text = get_attribute(pin_body, "capacitance")

            capacitance = 0.0

            if capacitance_text != "":
                capacitance = float(capacitance_text)


            pin = {
                    "direction" : get_attribute(pin_body, "direction"),
                    "capacitance" : capacitance,
                    "timing" : []
                    }

            timing_blocks = extract_anonymous_blocks(pin_body, "timing")

            for timing_body in timing_blocks:
                timing = {
                        "related_pin" : get_attribute(timing_body, "related_pin"),
                        "timing_type" : get_attribute(timing_body, "timing_type"),
                        "cell_rise" : parse_table(timing_body, "cell_rise"),
                        "cell_fall" : parse_table(timing_body, "cell_fall"),
                        "rise_constraint" : parse_table(timing_body, "rise_constraint"),
                        "fall_constraint" : parse_table(timing_body, "fall_constraint")
                        }

                pin["timing"].append(timing)

            # store the completed pin inside the current cell
            cell["pins"][pin_name] = pin

        #store the completed cell inside the library
        library["cells"][cell_name] = cell

    return library


def parse_declaration(line, declaration_type):
    '''
    Gets the signal names from one verilog input, output, or wire declaration

    Ignores Verilog type words such as wire, reg, and logic

    Input:
        line: one verilog line
        declaration_type: "input", "output", or "wire"

    Output:
        A list containing ths signal names

    Example:
        parse_declaration("input wire a, b;", "input")

    returns:
        ["a", "b"]
    '''
    
    # replace punctuation with spaces so split() produces clean words
    cleaned = line.replace(",", " ")
    cleaned = cleaned.replace(";", " ")

    pieces = cleaned.split()
    names = []
    found_type = False

    for piece in pieces:
        if piece == declaration_type:
            found_type = True

        # ignore words that describe signal's Verilog type
        elif(found_type and piece != "wire" and piece != "reg" and piece != "logic"):
            names.append(piece)

    return names


def parse_connections(instance_text):
    '''
    Gets named pin-to-net connections from one Verilog cell instance

    Named Verilog connections use this format:
        .PIN(net)

    Input:
        instance_text: the complete text of one gate or flip-flop instance

    Output:
        A dictionary mapping pin names to connected net names

    Example:
        .A(n2), .B(n5), .Y(d)

    becomes:
        {
            "A": "n2",
            "B": "n5",
            "Y": "d"
        }
    '''
    connections = {}
    position = 0

    while True:

        # every named connection starts with a period
        dot = instance_text.find(".", position)

        if dot == -1:
            break

        # in .A(n2), this finds the parenthesis after A
        opening = instance_text.find("(", dot)

        if opening == -1:
            break

        closing = instance_text.find(")", opening)

        if closing == -1:
            break

        # gets the pin and new names
        pin_name = instance_text[dot + 1:opening].strip()

        net_name = instance_text[opening + 1:closing].strip()

        if pin_name != "" and net_name != "":
            connections[pin_name] = net_name

        # continue searching after the current connection
        position = closing + 1

    return connections


def parse_verilog(filename):
    '''
    Parses a structural Verilog netlist and creates a circuit dictionary

    The dictionary stores:
        1. The module name
        2. Primary inputs
        3. Primary outputs
        4. Internal wires
        5. Cell instances
        6. Pin-to-net connections for every cell instance

    Input:
        filename: the name or path of the Verilog file

    Output:
        A dictionary representing the circuit
    '''
    text = remove_comments(read_file(filename))

    # process the file one late at a time
    lines = text.splitlines()

    circuit = {
            "module" : "",
            "inputs" : [],
            "outputs" : [],
            "wires" : [],
            "instances" : {}
    }

    # these variables collect a cell instance that has multiple lines
    current_cell_type = ""
    current_instance_name = ""
    current_instance_text = ""

    for original_line in lines:
        line = original_line.strip()

        if line == "":
            continue

        # continue collecting a multi-line instance
        if current_instance_name != "":
            current_instance_text += " " + line

            # ); marks the end of the instance
            if ");" in line:
                connections = parse_connections(current_instance_text)

                circuit["instances"][current_instance_name] = {
                        "cell_type" : current_cell_type,
                        "connections" : connections
                }

                current_cell_type = ""
                current_instance_name = ""
                current_instance_text = ""

            continue

        # read the module name
        if line.startswith("module "):
            rest = line[len("module "):]
            opening = rest.find("(")

            if opening == -1:
                circuit["module"] = rest.strip()

            else:
                circuit["module"] = rest[:opening].strip()

        # read primary inputs
        elif line.startswith("input "):
            names = parse_declaration(line, "input")

            for name in names:
                if name not in circuit["inputs"]:
                    circuit["inputs"].append(name)

        #read primary outputs
        elif line.startswith("output "):
            names = parse_declaration(line, "output")

            for name in names:
                if name not in circuit["outputs"]:
                    circuit["outputs"].append(name)

        # read internal wires
        elif line.startswith("wire "):
            names = parse_declaration(line, "wire")

            for name in names:
                if name not in circuit["wires"]:
                    circuit["wires"].append(name)

        elif line.startswith("endmodule"):
            continue

        else:

            # a remaining line containing ( may begin a cell instance
            opening = line.find("(")

            if opening == -1:
                continue

            beginning = line[:opening].strip()
            pieces = beginning.split()

            # the beginning should contain a cell type and instance namew
            if len(pieces) != 2:
                continue

            current_cell_type = pieces[0]
            current_instance_name = pieces[1]
            current_instance_text = line

            # handle a cell instance written entirely on one line
            if ");" in line:
                connections = parse_connections(current_instance_text)
                circuit["instances"][current_instance_name] = {
                        "cell_type" : current_cell_type,
                        "connections" : connections
                }

                current_cell_type = ""
                current_instance_name = ""
                current_instance_text = ""

    if current_instance_name != "":
        print("Error: incomplete instance", current_instance_name)
        sys.exit(1)

    return circuit


def parse_sdc(filename):
    '''
    Parses the sdc file and gets the clock information from creat_clock

    Command:
        create_clock -period 500 -name clock1 [get_ports clk]

    Input:
        filename: the name of the SDC file

    Output:
        Dictionary:
            name:
                the name of the clock

            port:
                the verilog input ports that recieves the clock

            period:
                the clock period

        Example:
            {
                "name": "clock1",
                "port": "clk"
                "period": 500.0
            }
    '''
    text = remove_comments(read_file(filename))

    cleaned = text.replace("[", " ")
    cleaned = cleaned.replace("]", " ")
    cleaned = cleaned.replace(";", " ")

    pieces = cleaned.split()

    clock = {
            "name": "",
            "port": "",
            "period": 0.0
    }

    position = 0

    while position < len(pieces):
        if pieces[position] == "-period":
            if position + 1 >= len(pieces):
                print("Error: missing clock from SDC file")
                sys.exit(1)

            try:
                clock["period"] = float(pieces[position + 1])

            except ValueError:
                print("Error: invalid clock period", pieces[position + 1])
                sys.exit(1)

            position += 2

        elif pieces[position] == "-name":
            if position + 1 >= len(pieces):
                print("Error: missing clock name in SDC file")
                sys.exit(1)

            clock["name"] = pieces[position + 1]
            position += 2

        elif pieces[position] == "get_ports":
            if position + 1 >= len(pieces):
                print("Error: missing clock port in SDC file")
                sys.exit(1)

            clock["port"] = pieces[position + 1]
            position += 2
        else:
            position += 1
    
    if clock["period"] <= 0.0:
        print("Error: not a valid clock period")
        sys.exit(1)

    if clock["port"] == "":
        print("Error: does not contain a clock port")
        sys.exit(1)

    return clock


def build_nets(circuit, library):
    '''
    Builds information about every net in the circuit by combining netlist and cell library

    Net is a wire that connects output pin to one or more input pins

    Every net includes:
        driver: output pin that drives the net
        loads: input pings that recieve the signal from the net
        capacitance: the total input capacitance of all load pins

    Input:
        circuit: the dictionary from parse_verilog()
        library: the dictionary from parse_liberty()
    
    Output:
        dictionary containing connectivity and capacitance
    '''

    nets = {}

    # creating entries for every verilog signal
    all_nets = (circuit["inputs"] + circuit["outputs"] + circuit["wires"])

    for net_name in all_nets:
        if net_name not in nets:
            nets[net_name] = {
                    "driver": None,
                    "loads": [],
                    "capacitance": 0.0
            }

    # Go through every cell instance in circuit
    for instance_name in circuit["instances"]:
        instance = circuit["instances"][instance_name]

        cell_type = instance["cell_type"]
        connections = instance["connections"]

        if cell_type not in library["cells"]:
            print("Error : cell", cell_type, "not found in Liberty file")
            sys.exit(1)

        cell = library["cells"][cell_type]
        
        # look at every pin connection
        for pin_name in connections:
            net_name = connections[pin_name]

            # making sure it has an entry
            if net_name not in nets:
                nets[net_name] = {
                        "driver": None,
                        "loads": [],
                        "capacitance" : 0.0
                }

            # make sure its in library cell
            if pin_name not in cell["pins"]:
                print("Error: pin", pin_name, "not found on cell", cell_type)
                sys.exit(1)

            pin = cell["pins"][pin_name]
            direction = pin["direction"]

            # output pin drives the net
            if direction == "output":
                nets[net_name]["driver"] = {
                        "instance": instance_name,
                        "pin": pin_name
                }
            
            # input pin is load on the net
            # capacitance of every input pin connection to it
            elif direction == "input":
                nets[net_name]["loads"].append({"instance": instance_name, "pin": pin_name})
                nets[net_name]["capacitance"] += pin["capacitance"]

    return nets

def interpolate_delay(table, capacitance_indices, capacitance):
    '''
    Calculates a timing delay based on the output load capacitance

    Liberty delay table has delay values at specific capacitances. If the actual capacitance 
    is between those two values, this function uses interpolation to estimate the delay.

    Since this is a simplified version, only rhe first row of the 2x2 table is used

    Input:
        table: 2x2 liberty table
        capacitance_indices: the two capacitance values from index_2 of the delay template
        capacitance: actual capacitance of the net

    Output:
        The estimated delay

    Example:
        capacitance_indices = [5.0, 30.0]
        table = [
            [50.0, 100.0],
            [75.0, 200.0]
        ]

        If the capacitance is 17.5 ff, the delay will be halfway between 50 and 100 = 75 ps.
    '''

    # make sre the table and capacitance indices contain the values
    if len(table) != 2 or len(capacitance_indices) != 2:
        print("Error: invalid delay table")
        sys.exit(1)

    # the capacitance points from liberty index_2
    capacitance_1 = capacitance_indices[0]
    capacitance_2 = capacitance_indices[1]

    # using the first row
    delay_1 = table[0][0]
    delay_2 = table[0][1]

    # if load is smaller -> use first delay point
    if capacitance <= capacitance_1:
        return delay_1

    # if load is larger -> use second delay point
    if capacitance >= capacitance_2:
        return delay_2

    # find how far the capacitance is between the two points
    fraction = ((capacitance - capacitance_1) / (capacitance_2 - capacitance_1))

    #estimate delay
    delay = (delay_1 + fraction * (delay_2 - delay_1))

    return delay


def find_timing_arc(cell, input_pin, output_pin):
    '''
    Finds the liberty timing arc from a specific input pin to a specific output pin of a cell

    Liberty stores timing information inside the output pin

    Input:
        cell: the liberty information for one cell
        input_pin: the input pin where the signal enters the cell
        output_pin: the output pin where the signal leaves the cell

    Output:
        the timing dictionary for the meatching timing arc
    '''

    # make sure the output pin exists on this cell
    if output_pin not in cell["pins"]:
        return None

    output = cell["pins"][output_pin]

    # look through all timing arcs stored on output pin
    for timing in output["timing"]:
        if timing["related_pin"] == input_pin:
            return timing
    
    return None

def get_cell_delay(library, cell_type, input_pin, output_pin, capacitance):
    '''
    Calculates the delay through a combinational cell from one pin to output pin

    Function finds the correct Liberty timing arc, calculates both rise delay and fall delay
    using the load capacitance, and returns the larger of the two delays

    Input:
        library: the dictionary retuned by parse_liberty()
        cell_type: the type of cell
        input_pin: the pin where the signal enters the cell
        output_pin: the pin where the signal leaves the cell
        capacitance: the total load capacitance connected to the output net

    Output:
        the worse-case delay through the cell
    '''

    # make sure the cell exists in the liberty library
    if cell_type not in library["cells"]:
        print("Error: cell", cell_type, "not found in Liberty file")
        sys.exit(1)

    cell = library["cells"][cell_type]

    # find the timing information for input -> output path
    timing = find_timing_arc(cell, input_pin, output_pin)

    if timing is None:
        print("Error: no timing arc from", input_pin, "to", output_pin, "on", cell_type)
        sys.exit(1)

    # get the capacitance values from delay table
    capacitance_indices = (library["delay_template"]["index_2"])

    #calculated the rise delay and fall delay at the output capacitance
    rise_delay = interpolate_delay(timing["cell_rise"], capacitance_indices, capacitance)
    fall_delay = interpolate_delay(timing["cell_fall"], capacitance_indices, capacitance)

    # use the larger delay for worst_case
    delay = max(rise_delay, fall_delay)

    return delay


def get_clock_to_q_delay(library, cell_type, output_pin, capacitance):
    '''
    Calculates the clock_to_Q delay of flip_flop

    Clock_to_Q de;ay is the amount of time between the active clock_edge and the flip_flop output
    changing.

    The delay also depends on the load capacitance connected to the flip_flop output

    Input:
        library: the dictionary from parse_liberty()
        cell_type: the type of flip_flop
        output_pin: the output pin of the flip_flop -> Q
        capacitance: the total load capacitance connected to output net

    Output:
        worse case clock-to-Q delay
    '''

    # make sure the flip-flop exists
    if cell_type not in library["cells"]:
        print("Error: cell", cell_type, "not found in Liberty file")
        sys.exit(1)

    cell = library["cells"][cell_type]

    # make sure the output pin exists
    if output_pin not in cell["pins"]:
        print("Error: pin", output_pin, "not found on", cell_type)
        sys.exit(1)

    output = cell["pins"][output_pin]

    timing = None

    # find the clock-to-Q timing arc stored on the output pin
    for arc in output["timing"]:
        if(arc["timing_type"] == "rising_edge" or arc["timing_type"] == "falling_edge"):
            timing = arc
            break

    if timing is None:
        print("Error: no clock-to-Q timing fouind on", cell_type, output_pin)
        sys.exit(1)
    
    # get the capacitance points from the liberty file
    capacitance_indices = (library["delay_template"]["index_2"])

    # calculate the Q rising delay
    rise_delay = interpolate_delay(timing["cell_rise"], capacitance_indices, capacitance)

    # calaculate the Q falling delay
    fall_delay = interpolate_delay(timing["cell_fall"], capacitance_indices, capacitance)

    # use the slowest for worse-case timing
    delay = max(rise_delay, fall_delay)

    return delay

def get_setup_time(library, cell_type, data_pin):
    '''
    Finds the setup time requirement for the data input of a flip_flop

    Setup time tells how long before the active clock edge the data must be stable at
    flip-flop input

    Take the largest value from rise contraint and fall constraint tables

    Input:
        library: dictionary from parse_liberty()
        cell_type: the type of flip-flop
        data_pin: the data input pin of the flip-flop -> D

    Output:
        worst case setup time
    '''

    # make sure the flip-flop exists
    if cell_type not in library["cells"]:
        print("Error: cell", cell_type, "not found in Liberty file")
        sys.exit(1)

    cell = library["cells"][cell_type]

    # make sure the data pin exists on the flip-flop
    if data_pin not in cell["pins"]:
        print("Error: pin", data_pin, "not found on", cell_type)
        sys.exit(1)

    pin = cell["pins"][data_pin]

    setup_values = []

    # look through the timing information on data pin
    for timing in pin["timing"]:
        if timing["timing_type"].startswith("setup"):
            for row in timing["rise_constraint"]:
                for value in row:
                    setup_values.append(value)

            for row in timing["fall_constraint"]:
                for value in row:
                    setup_values.append(value)

    if len(setup_values) == 0:
        print("Error: no setup timing found for", cell_type, data_pin)
        sys.exit(1)

    setup_time = max(setup_values)

    return setup_time


def propagate_arrival_times(circuit, library, nets):
    '''
    Calcluates the arrival time of the signal at every net in the circuit
    
    Primary inputs start with an arrival time of 0

    Flip-flop output nets start with their clock-to-Q delay

    Function moves thorugh combinational gates. For each gate, it calculates the arrival time
    through every input-to-output timing arc and keeps the largest arrival time

    Input:
        circuit: the dictionary from parse_verilog()
        library: the dicitonary from parse_liberty()
        nets: the dictionary from build_nets()

    Output:
        arrival_times: dictionary storing the arrival time of every net
        previous: storing where the worst-case arrival came from
    '''

    arrival_times = {}
    previous = {}

    # the arrival times for every net is not known
    for net_name in nets:
        arrival_times[net_name] = None
        previous[net_name] = None

    # primary inputs start at time 0
    for net_name in circuit["inputs"]:
        arrival_times[net_name] = 0.0

    # flip-flop outputs start with their clock-to-Q delay
    for instance_name in circuit["instances"]:
        instance = circuit["instances"][instance_name]

        cell_type = instance["cell_type"]
        connections = instance["connections"]

        cell = library["cells"][cell_type]

        if cell["sequential"]:
            # look for output pins such as Q
            for pin_name in connections:
                if cell["pins"][pin_name]["direction"] == "output":
                    output_net = connections[pin_name]

                    capacitance = nets[output_net]["capacitance"]

                    delay = get_clock_to_q_delay(library, cell_type, pin_name, capacitance)

                    arrival_times[output_net] = delay

                    previous[output_net] = {
                            "instance":instance_name,
                            "input_net": None,
                            "input_pin": "CLK",
                            "output_pin": pin_name,
                            "delay" : delay
                    }

    processed = []

    while True:
        progress = False

        # go through every instance in the circuit
        for instance_name in circuit["instances"]:

            if instance_name in processed:
                continue

            instance = circuit["instances"][instance_name]

            cell_type = instance["cell_type"]
            connections = instance["connections"]

            cell = library["cells"][cell_type]

            if cell["sequential"]:
                continue

            input_pins = []
            output_pins = []

            for pin_name in connections:
                if cell["pins"][pin_name]["direction"] == "input":
                    input_pins.append(pin_name)

                elif cell["pins"][pin_name]["direction"] == "output":
                    output_pins.append(pin_name)

            ready = True

            # every input have an arrival time before calculate gate's output arrival time
            for input_pin in input_pins:
                input_net = connections[input_pin]

                if arrival_times[input_net] is None:
                    ready = False

            if not ready:
                continue

            # calculate each output of the gate
            for output_pin in output_pins:
                output_net = connections[output_pin]

                capacitance = nets[output_net]["capacitance"]

                best_arrival = None
                best_input_pin = None
                best_input_net = None
                best_delay = None

                # try the timing path from every input to this output
                for input_pin in input_pins:
                    input_net = connections[input_pin]

                    delay = get_cell_delay(
                            library,
                            cell_type,
                            input_pin,
                            output_pin,
                            capacitance
                    )

                    candidate_arrival = (arrival_times[input_net] + delay)

                    # keep the path with largest arrival time
                    if(best_arrival is None or candidate_arrival > best_arrival):
                        best_arrival = candidate_arrival
                        best_input_pin = input_pin
                        best_input_net = input_net
                        best_delay = delay

                arrival_times[output_net] = best_arrival

                previous[output_net] = {
                        "instance": instance_name,
                        "input_net": best_input_net,
                        "input_pin": best_input_pin,
                        "output_pin": output_pin,
                        "delay": best_delay
                }

            processed.append(instance_name)
            progress = True
            
        # if went throug very gate then nothing left
        if not progress:
            break

    return arrival_times, previous

def collect_timing_paths(circuit, library, arrival_times, previous):
    '''
    Collects register-to-register timing paths in the circuit

    Function looks for data input pins of flip-flops. It checks the arrival time of the
    connected net and traces the path backwards

    Only paths that begin at another flip-flop are stored

    The setup time of the ending flio-flop is added to the arrival time to get the total timing

    Input:
        circuit: the dictionary returned by parse_verilog()
        library: the dictionary from parse_liberty()
        arrival_times: the arrival time dictionary from propagate_arrival_times()
        previous: previous path dictionary

    Output:
        List containing information about register-to-register timing path
    '''

    paths = []

    # look through every instance for ending flip-flops
    for instance_name in circuit["instances"]:
        instance = circuit["instances"][instance_name]

        cell_type = instance["cell_type"]
        connections = instance["connections"]

        cell = library["cells"][cell_type]

        # only want flip-flops as endpoints
        if not cell["sequential"]:
            continue

        # look through the pins
        for pin_name in connections:
            pin = cell["pins"][pin_name]

            # check whether has setup timing constraint
            has_setup = False

            for timing in pin["timing"]:
                if timing["timing_type"].startswith("setup"):
                    has_setup = True
                    break

            # pins like clk and q are not data endpoints
            if not has_setup:
                continue

            end_net = connections[pin_name]

            # cannot use path if arrival time is unknown
            if(end_net not in arrival_times or arrival_times[end_net] is None):
                continue

            setup_time = get_setup_time(library, cell_type, pin_name)
            arrival_time = arrival_times[end_net]

            # tracing backwards from ending net
            path = [end_net]

            cell_delays = []

            current_net = end_net
            start_instance = None

            while True:
                step = previous[current_net]
                
                #if no previous gate, path came from primary input
                if step is None:
                    break

                path.append(step["instance"])
                cell_delays.append({"instance": step["instance"], "delay": step["delay"]})

                # instance_net = None means reached Q output of the flip-flop
                if step["input_net"] is None:
                    start_instance = step["instance"]
                    break

                current_net = step["input_net"]
                path.append(current_net)

            # ignore paths that don't begin at flip-flop
            if start_instance is None:
                continue

            # traversed backwards so flip
            path.reverse()
            cell_delays.reverse()

            # add ending flip-flop
            path.append(instance_name)

            total_delay = arrival_time + setup_time

            paths.append({
                "start_instance": start_instance,
                "end_instance": instance_name,
                "end_pin": pin_name,
                "end_net": end_net,
                "arrival_time": arrival_time,
                "setup_time": setup_time,
                "total_delay": total_delay,
                "path": path,
                "cell_delays": cell_delays
            })

    return paths


def find_critical_path(paths):
    '''
    Find the slowest path/largest delay

    Input:
        paths: the list returned by timing paths

    Output:
        dictionary with critical path
    '''

    if len(paths) == 0:
        return None

    critical_path = paths[0]

    for path in paths:
        if path["total_delay"] > critical_path["total_delay"]:
            critical_path = path

    return critical_path


def main():
    '''
    Runs the timing analysis

    1. Reads the liberty, Verilog, and SDC file
    2. Builds the circuits nets
    3. Calculates arrival times
    4. Collects timing paths
    5. Finds critical paths
    6. Compares critical path to clock period
    7. Prints the results
    '''
    
    liberty_file = "cells.lib"
    verilog_file = "koba.v"
    sdc_file = "koba.sdc"

    # parse the files
    library = parse_liberty(liberty_file)
    circuit = parse_verilog(verilog_file)
    clock = parse_sdc(sdc_file)

    # build information about drivers, loads, and capacitances
    nets = build_nets(circuit, library)

    # calculate when signal reaches nets
    arrival_times, previous = propagate_arrival_times(circuit, library, nets)

    # build timing paths
    paths = collect_timing_paths(circuit, library, arrival_times, previous)

    # find largest total delay path
    critical_path = find_critical_path(paths)

    # make sure at least one path was found
    if critical_path is None:
        print("No register-to-register timing path was found")
        return

    clock_period = clock["period"]
    total_delay = critical_path["total_delay"]

    # slack is how much margin is left
    slack = clock_period - total_delay

    print()
    print("Static Timing Analysis")
    print()
    print("Critical path:", " -> ".join(critical_path["path"]))

    for cell_info in critical_path["cell_delays"]:
        print(cell_info["instance"], ":", round(cell_info["delay"], 2), "ps")

    print(critical_path["end_instance"], "setup:", round(critical_path["setup_time"], 2), "ps")
    print("Start flip-flop:", critical_path["start_instance"])
    print("End flip-flop:", critical_path["end_instance"])
    print("Arrival time:", critical_path["arrival_time"], "ps")
    print("Setup time:", critical_path["setup_time"], "ps")
    print("Total delay:", total_delay, "ps")
    print("Clock period:", clock_period, "ps")
    print("Slack:", round(slack, 2), "ps")

    if slack >= 0:
        print("Timing: PASS")
    else:
        print("Timing: FAIL")

if __name__ == "__main__":
    main()




