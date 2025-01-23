import sys

def load_pmp_config(file_path):

    pmp_config_addr = []
    pmp_config_addr_0x = []
    pmp_config_read = []
    pmp_config_write = []
    pmp_config_fetch = []
    pmp_config_range = []
    pmp_config_lock = []

    with open(file_path,'r') as file:
        for line_number, line in enumerate(file):
            stripped_line = line.strip()
            if stripped_line.startswith('0x'):
                hex_value = stripped_line[2:]

                if line_number < 64:
                    hexToInt = int(hex_value,16)
                    intToBin = [(hexToInt >> i) & 1 for i in range(7,-1,-1)]
                    read_config = intToBin[0]
                    write_config = intToBin[1]
                    fetch_config = intToBin[2]
                    range_config = 2*intToBin[4] + intToBin[3]
                    #No checking here, assume input of bit[6:5] is correct, i.e. 2'b0
                    lock_config = intToBin[7]
                    pmp_config_read.append(read_config)
                    pmp_config_write.append(write_config)
                    pmp_config_fetch.append(fetch_config)
                    pmp_config_range.append(range_config)
                    pmp_config_lock.append(lock_config)
                else:
                    #print(f"Convert pmp[{line_number-64}] 0x:{hex_value} 0b:{format(int(hex_value,16), '032b')} Config lock:{pmp_config_lock[line_number-64]} range:{pmp_config_range[line_number-64]} read:{pmp_config_read[line_number-64]} write:{pmp_config_write[line_number-64]} fetch:{pmp_config_fetch[line_number-64]}")
                    pmp_config_addr.append(int(hex_value,16))
                    pmp_config_addr_0x.append(format(int(hex_value,16), '032b'))
            else :
                raise ValueError(f"Line {line_number+1} config format invalid at line:{stripped_line} ")
        
    return pmp_config_read, pmp_config_write, pmp_config_fetch, pmp_config_range, pmp_config_lock, pmp_config_addr, pmp_config_addr_0x

def check_access(pmp_config_read, pmp_config_write, pmp_config_fetch, pmp_config_range, pmp_config_lock, pmp_config_addr, pmp_config_addr_0x, physical_addr,privilege_mode,operation) :
    #initalize local variable: 
    # previous address as 0, anyPMPEnabled = 0
    previous_addr = 0
    any_PMP_enabled = 0
    # for i from 0 to 63
    for i in range(64):
        addr_in_range = 0
    # check if any PMP is enabled
    # get address range of pmpaddr + pmp_config_range 
    # pmp_config_range:
    # 0: disabled, skip, if anyone not 0, anyPMPEnabled = 1
    # 1: Top of range, previous address <= addr < pmpaddr
    # 2: NA4, 4-bytes start from pmp addr, pmpaddr <= addr < pmpaddr + 3
    # 3: NAPOT: read pmpaddr as two parts, seperated by 0
    # yyyy...y011: base = yyyy...y000, range: 2^(3 + count(number of 1 after 0))
    # yyyy...y000 <= addr < yyyy...y000 + 2^(3+n)-1
    # Remarks: remember to start reading from LSB, MSB may have 0s like 100111001...
        if(pmp_config_range[i] == 0) :
            continue
        elif(pmp_config_range[i] == 1) :
            if(previous_addr < pmp_config_addr[i]) :
                any_PMP_enabled = 1
            addr_in_range = (previous_addr <= physical_addr) & (physical_addr < pmp_config_addr[i])
        elif(pmp_config_range[i] == 2) :
            any_PMP_enabled = 1
            addr_in_range = (pmp_config_addr[i] <= physical_addr) & (physical_addr < pmp_config_addr[i] + 4)
        elif(pmp_config_range[i] == 3) :
            any_PMP_enabled = 1
            j = 31
            num_of_byte = 8
            while(pmp_config_addr_0x[i][j] != '0'):
                pmp_config_addr_0x[i] = (pmp_config_addr_0x[i][:j] + '0' + pmp_config_addr_0x[i][j + 1:])
                num_of_byte = num_of_byte * 2
                j = j - 1
                if j == -1:
                    break
            start_addr = int(pmp_config_addr_0x[i], 2)
            addr_in_range = (start_addr <= physical_addr) & (physical_addr < (start_addr + num_of_byte))
        else :
            print(f"PMP range config read error: value{pmp_config_range[i]} should be 0-3")
        
        previous_addr = pmp_config_addr[i]

    # check whether physical addr in range
    # if not, skip to next one
    # else, check permission
    # 1.L bit, if L=1, M-mode need to check for R/W/X permission
    # 1.1 if L=0, M-mode access always success, S/U-mode check R/W/X premission
    # if the physical addr is not in range of any pmp addr config:
    # M-mode success, S/U-mode success if all pmpconfig is disabled(create a flag to save whether atleast one is programmed), else fail
        if addr_in_range :
            #print(f"Address matched reg[{i}], request target:{physical_addr} config_addr:{pmp_config_addr[i]}")
            #print(f"Config lock:{pmp_config_lock[i]} range:{pmp_config_range[i]} read:{pmp_config_read[i]} write:{pmp_config_write[i]} fetch:{pmp_config_fetch[i]}")
            if(pmp_config_lock[i] == 1):
                if(operation == 'R'):
                    if(pmp_config_read[i]) :
                        return 0
                    else :
                        return 1
                elif(operation == 'W') :
                    if(pmp_config_write[i]) :
                        return 0
                    else :                      
                        return 1
                elif(operation == 'X') :
                    if(pmp_config_fetch[i]) :
                        return 0
                    else :
                        return 1
            else :
                if(privilege_mode == 'M') :
                    return 0
                else :
                    if(operation == 'R'):
                        if(pmp_config_read[i]) :
                            return 0
                        else :
                            return 1
                    elif(operation == 'W') :
                        if(pmp_config_write[i]) :
                            return 0
                        else :                      
                            return 1
                    elif(operation == 'X') :
                        if(pmp_config_fetch[i]) :
                            return 0
                        else :
                            return 1
        else :
            if (i == 63):
                #print("No address matched, try pprivilege_mode checking or no register enabled checking")
                if privilege_mode == 'M' :
                    return 0
                else :
                    return any_PMP_enabled
            else:
                continue

def main(args):
    if len(args) != 4:
        print("Please provide exactly four arguments.")
        return

    config_file, physical_addr_str, privilege_mode, operation = args
    #print("Arguments received:")
    #print(f"1: {config_file}")
    #print(f"2: {physical_addr_str}")
    #print(f"3: {privilege_mode}")
    #print(f"4: {operation}")

    if not physical_addr_str.startswith("0x") :
        print("Physical address must start with '0x'.")
        return

    if not privilege_mode.startswith(("M","S","U")) :
        print("Privilege mode must be 'M', 'S', or 'U'.")
        return
    
    if not operation.startswith(("R","W","X")) :
        print("Operation must be 'R', 'W', or 'X'.")
        return
    
    try:
        pmp_config_read, pmp_config_write, pmp_config_fetch, pmp_config_range, pmp_config_lock, pmp_config_addr, pmp_config_addr_0x = load_pmp_config(config_file)
    except ValueError as e:
        print(f"Error loading config file: {e}")
        return

    physical_addr = int(physical_addr_str,16)

    fault = check_access(pmp_config_read, pmp_config_write, pmp_config_fetch, pmp_config_range, pmp_config_lock, pmp_config_addr, pmp_config_addr_0x, physical_addr,privilege_mode,operation)

    if fault:
        print("Access failed")
    else :
        print("Access success")

if __name__ == "__main__":
    main(sys.argv[1:])