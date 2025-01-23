import random


# generate pmp address
# 1. 32-bit random
# 2. conversion




def generate_random_binary_parameters():
    # Generate three random binary parameters (1 bit each)
    lock = random.randint(0, 1)
    range_0 = random.randint(0, 1)
    range_1 = random.randint(0,1)
    fetch = random.randint(0, 1)
    write = random.randint(0, 1)
    read = random.randint(0, 1)

    return lock, range_1, range_0, fetch, write, read

def concatenate_to_binary(lock, range_1, range_0, fetch, write, read):
    # Concatenate the binary parameters into a single binary number
    x = f"{lock}00{range_1}{range_0}{fetch}{write}{read}"  # This creates a string representation
    return x

def convert_to_hexadecimal(binary_str):
    # Convert the binary string to an integer, then to hexadecimal
    x_int = int(binary_str, 2)  # Convert binary string to integer
    x_hex = hex(x_int)  # Convert integer to hexadecimal
    return x_hex

def write_to_file(hex_value):
    with open('config.txt', 'w') as file:
        file.write(hex_value + '\n')  # Write the hex value to the file

def main():
    hex_values = []  # List to store hex values for all iterations

    for _ in range(64):  # Loop for 64 times
        lock, range_1, range_0, fetch, write, read = generate_random_binary_parameters()  # Generate parameters
        binary_str = concatenate_to_binary(lock, range_1, range_0, fetch, write, read)  # Concatenate to binary
        hex_value = convert_to_hexadecimal(binary_str)  # Convert to hexadecimal
        hex_values.append(hex_value)  # Store hex value

    #...another loop for line 64 to 128...
    for _ in range(64):
        addr = random.randint(0,2**32-1)
        hex_value = hex(addr)
        hex_values.append(hex_value)

    # Write all hex values to the file, replacing previous content
    with open('config.txt', 'w') as file:
        for hex_value in hex_values:
            print(f"writing{hex_value}")
            file.write(hex_value + '\n')  # Write each hex value to the file

    #print("Generated hexadecimal values:")
    #for hex_value in hex_values:
    #    print(hex_value)

if __name__ == "__main__":
    main()