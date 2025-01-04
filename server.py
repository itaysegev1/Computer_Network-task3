import socket
import threading
import time

YELLOW = "\033[93m"  # For resending Ack
RED = "\033[91m"  # For Errors
GREEN = "\033[92m"  # For sending Ackes
BLUE = "\033[94m"  # For finished sending all
PURPLE = "\033[95m"  # For start and end operations
CYAN = "\033[96m"  # For resiving segments
RESET = "\033[0m"
"""
General explanation of the logistics parts:
    what we did in this project is that we seperated every functionality we needed into methods,
    in order for the code to be organised and easy to read.
    At the beginning of every method there is a documentation of what the function does and what it's supposed 
    to return.
    the general explanation of the code and structer is in the attached PDF of this project.
"""

"""Here we gave the default IP and PORT we will use to create the connection, and we used a global variable to keep 
track of the maximum length of the message the server can handle"""
host = '127.0.0.1'
port = 1234
DEFAULT_MAX_MESSAGE_LENGTH = 15
MAX_MESSAGE_LENGTH = 1024
WINDOW_SIZE = 0
DEFAULT_HEADER_SIZE = 3
HEADER_SIZE = 1024

# ----------------------------------------------------------------------------------------------------------------------
"""We will access this function ONLY if the client chose to use the files! Methods Goal: This function opens a file 
and reads its content. It searches for a line starting with "maximum_msg_size:", splits by ":"  and keeps the number 
after the colon, and keeps it to the global variable `MAX_MESSAGE_LENGTH`, from now on this is the capacity of the 
servers messages length"""


def read_from_file(path):
    global MAX_MESSAGE_LENGTH
    try:
        with open(path, 'r', encoding='utf-8') as file:
            for line in file:
                if line.startswith("maximum_msg_size:"):
                    msg, maxes = line.rsplit(":", 1)
                    MAX_MESSAGE_LENGTH = int(maxes)
                    break
    except FileNotFoundError:
        MAX_MESSAGE_LENGTH = int(DEFAULT_MAX_MESSAGE_LENGTH)


# ----------------------------------------------------------------------------------------------------------------------

""""
Methods Goal:
    This function reads data from the specified client socket, using the global `MAX_MESSAGE_LENGTH` 
    to determine the maximum amount of data to receive. The received data is then decoded from bytes 
    to a string.
Returns:
    the function returns the decoded data as string or None if the server failed to receive the data

"""


def receive_client_request(client_socket):
    global MAX_MESSAGE_LENGTH, WINDOW_SIZE
    try:
        data = client_socket.recv(int(MAX_MESSAGE_LENGTH) + int(HEADER_SIZE))
        try:
            message = data.decode('utf-8')
        except UnicodeDecodeError:
            message = data.decode('utf-8', errors='replace')
        return message
    except Exception as e:
        print(f"{RED}Failed to receive client request: {e}{RESET}")
        return None


# ----------------------------------------------------------------------------------------------------------------------
"""
Methods Goal:
    This function determines the number of digits in the input `number` by repeatedly dividing 
    it by 10 until it reaches 0.
Returns:
    The number of digits in the input number as an integer

"""


def cal_number_seg_size(number) -> int:
    count = 0
    x = number
    while x != 0:
        count += 1
        x = x // 10
    return count


# ----------------------------------------------------------------------------------------------------------------------
"""Methods Goal: This function examines the input  and performs actions based on the requests content, If the request 
is "max", it sets `MAX_MESSAGE_LENGTH` to the default number we put at the beginning of the file and if the request 
starts with "max_file", it extracts a file path, reads the file using `read_from_file` method , and updates 
`MAX_MESSAGE_LENGTH` with what was written in the file. 
Return: the function returns the strig of the value of  'MAX_MESSAGE_LENGTH
        or returns the string of the request as we got it"""


def check_client_request(request) -> str:
    global MAX_MESSAGE_LENGTH, WINDOW_SIZE, HEADER_SIZE
    if request == "max":
        return str(MAX_MESSAGE_LENGTH)
    elif request.startswith("max_file"):
        x, path = request.rsplit(":", 1)
        read_from_file(path)
        return str(MAX_MESSAGE_LENGTH)
    elif request.startswith("window size:"):
        try:
            _, num = request.rsplit(":", 1)
            WINDOW_SIZE = int(num)
            HEADER_SIZE = cal_number_seg_size(WINDOW_SIZE) + 1
        except ValueError:
            print(f"{RED}Failed to extract window size from request: {request} taking default...{RESET}")
            HEADER_SIZE = DEFAULT_HEADER_SIZE
        return str(HEADER_SIZE)

    else:
        return request


# ----------------------------------------------------------------------------------------------------------------------
""" 
Methods Goal:
    to send a message specified we finished the connection successfully or send an error.
Return: 
    the string according to the state at the end of the connection
"""


def msg_of_ending(client_socket, end_message):
    try:
        s = "Received All Segments Successfully"
        print(s)
        time.sleep(2)
        client_socket.sendall(s.encode('utf-8'))
        print(f"{BLUE}Received  all segments.txt! the final message is:\n {end_message}{RESET}")
    except Exception as e:
        print(f"{RED}Failed to send acknowledgment: {e}{RESET}")


# ----------------------------------------------------------------------------------------------------------------------
""" 
Methods Goal:
    sending Acks to the client and printing their status
"""


def send_ack(client_socket, ack_number):
    try:
        ack_message = f"ACK{ack_number}\\n"
        client_socket.sendall(ack_message.encode('utf-8'))
        print(f"{GREEN}Sent acknowledgment: {ack_number}{RESET}")
    except Exception as e:
        print(f"{RED}Failed to send acknowledgment: {e}{RESET}")


def real_number(expected, truelly):
    global WINDOW_SIZE
    real = expected % WINDOW_SIZE
    if real < truelly:
        return expected + (truelly - real)
    elif real > truelly:
        return expected - (truelly - real)
    else:
        return expected


# ----------------------------------------------------------------------------------------------------------------------
"""
Methods Goal:
    This function processes requests and message segments from a client using a reliable 
    transport protocol. It ensures segments are received in order, handles out-of-order 
    segments, and acknowledges received segments. Once all segments are received, it 
    connects the full message and sends it back to the client.
Returns:
    the full message and sends it back to the client.

"""


def client_handler(client_socket, client_address):
    global WINDOW_SIZE
    flag = False # need to be true for dropping 1 segments ack
    list_msg_in_order = []
    list_not_in_order = {}
    number_of_segments = 0
    print(f"{PURPLE}Connected to client: {client_address}{RESET}")
    with (client_socket):
        expected_sequence = 0
        while True:
            request = receive_client_request(client_socket)
            if not request:
                print(f"{PURPLE}Connection closed by client: {client_address}{RESET}")
                break
            if request.startswith("max"):
                response = check_client_request(request)
                client_socket.sendall(response.encode('utf-8'))
                print(f"{PURPLE}Sent maximum message size to client: {response}{RESET}")
            elif request.startswith("window size:"):
                response = check_client_request(request)
                client_socket.sendall(response.encode('utf-8'))
                print(f"{PURPLE}The header is in size of: {response}{RESET}")
            else:
                print(f"{CYAN}Received segment: {request}{RESET}")
                try:
                    segment_data, sequence_number = request.rsplit(":", 1)
                    sequence_number = int(sequence_number)
                    if sequence_number == -1:
                        number_of_segments = int(segment_data)
                        send_ack(client_socket, -1)
                    if sequence_number == (expected_sequence % WINDOW_SIZE):
                        if expected_sequence == 3 and flag:
                            print("Skipping sequence")
                            flag = False
                        else:
                            print(f"{CYAN}Segment {expected_sequence} received in order.{RESET}")
                            list_msg_in_order.append(segment_data)
                            send_ack(client_socket, expected_sequence % WINDOW_SIZE)
                            expected_sequence += 1
                            while expected_sequence in list_not_in_order.keys() and expected_sequence < number_of_segments:
                                print(f"{BLUE}Segment {expected_sequence} was in Buffer.{RESET}")
                                list_msg_in_order.append(list_not_in_order.pop(expected_sequence))
                                send_ack(client_socket, expected_sequence % WINDOW_SIZE)
                                expected_sequence += 1
                            list_not_in_order.clear()
                    elif sequence_number != -1:
                        print(
                            f"{RED}Out-of-order segment received. Resending ACK{expected_sequence % WINDOW_SIZE - 1}.{RESET}")
                        try:
                            real_seq_num = real_number(int(expected_sequence), int(sequence_number))
                            if real_seq_num < number_of_segments:
                                list_not_in_order[real_seq_num] = segment_data
                        except ValueError as ve:
                            print(f"{RED}Invalid {ve}{RESET}")
                        send_ack(client_socket, expected_sequence % WINDOW_SIZE - 1)
                    if number_of_segments == len(list_msg_in_order):
                        all_msg = ""
                        for msg in list_msg_in_order:
                            all_msg += msg
                        msg_of_ending(client_socket, all_msg)

                except ValueError as ve:
                    print(f"{RED}Error processing segment: {ve}{RESET}")


# ----------------------------------------------------------------------------------------------------------------------

"""Method Goal: this method is were we open the socket connection and connect to the client, basically this function 
is the connecting one to all the other ones, when we finish the whole process we close the socket."""


def server():
    print(f"{PURPLE}Starting server on {host}:{port}{RESET}")
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"{PURPLE}Server is listening for connections...{RESET}")

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"{YELLOW}New connection from {client_address}{RESET}")
            client_thread = threading.Thread(target=client_handler, args=(client_socket, client_address))
            client_thread.start()

    except Exception as e:
        print(f"{RED}Server error: {e}{RESET}")
    finally:
        server_socket.close()


if __name__ == '__main__':
    choice = 0
    while choice != "1" and choice != "2":
        choice = input("\t1.Read from a file.\n\t2.Enter manually Max message length.\n\t Enter your choice: ")
        if choice == "2":
            try:
                MAX_MESSAGE_LENGTH = int(input("Enter max message length: "))
            except Exception as ve:
                print(f"{RED}Invalid input... taking the default size {ve}{RESET}")
                MAX_MESSAGE_LENGTH = int(DEFAULT_MAX_MESSAGE_LENGTH)
    server()
