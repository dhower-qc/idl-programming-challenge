import sys

def main():
    # Parse command-line arguments
    if len(sys.argv) != 5:
        print("Usage: python3 pmp_check.py pmp_configuration.txt 0xaddress M/W/S R/W/X")
        sys.exit(1)

    config_file = sys.argv[1]
    address_str = sys.argv[2]
    mode = sys.argv[3].upper()
    operation = sys.argv[4].upper()

    # Validate physical address
    if not address_str.startswith("0x"):
        print("Invalid address format. Must start with '0x'.")
        sys.exit(1)
    try:
        address = int(address_str, 16)
    except ValueError:
        print("Invalid address format.")
        sys.exit(1)

    # Validate privilege mode and operation
    if mode not in ['M', 'S', 'U']:
        print("Invalid privilege mode. Must be one of 'M', 'S', or 'U'.")
        sys.exit(1)
    if operation not in ['R', 'W', 'X']:
        print("Invalid operation. Must be one of 'R', 'W', or 'X'.")
        sys.exit(1)

    # Map privilege modes to levels
    priv_level = {'M': 3, 'S': 1, 'U': 0}[mode]

    try:
        with open(config_file, 'r') as f:
            lines = f.read().splitlines()
            if len(lines) != 128:
                print("Configuration file must have exactly 128 lines.")
                sys.exit(1)
            pmpcfg = [int(line, 16) for line in lines[:64]]
            pmpaddr = [int(line, 16) for line in lines[64:]]
    except Exception as e:
        print(f"Error reading configuration file: {e}")
        sys.exit(1)

    # Define PMP region class
    class PMPRegion:
        def __init__(self, cfg, addr):
            self.cfg = cfg
            self.addr = addr
            self.a = (cfg >> 5) & 0x3  # Address match type
            self.r = (cfg >> 4) & 0x1  # Read permission
            self.w = (cfg >> 3) & 0x1  # Write permission
            self.x = (cfg >> 2) & 0x1  # Execute permission
            self.priv = (cfg >> 0) & 0x3  # Privilege level (assuming bits 1-0)

        def matches(self, addr):
            if self.a == 0:  # OFF
                return False
            elif self.a == 1:  # TOR
                return addr < self.addr
            elif self.a == 2:  # NA4
                return addr >= self.addr
            elif self.a == 3:  # NAND
                return (addr ^ self.addr) < self.addr
            return False

        def permits(self, op, priv):
            # Check operation permission
            if op == 'R' and not self.r:
                return False
            if op == 'W' and not self.w:
                return False
            if op == 'X' and not self.x:
                return False
            if priv >= self.priv:
                return True
            return False

    regions = [PMPRegion(pmpcfg[i], pmpaddr[i]) for i in range(64)]

    for region in regions:
        if region.matches(address):
            if region.permits(operation, priv_level):
                print("Access allowed")
                return
            else:
                print("Access fault")
                return

    print("Access fault")

if __name__ == "__main__":
    main()