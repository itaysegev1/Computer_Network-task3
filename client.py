import socket
import time

YELLOW = "\033[93m"  # For resending segments
RED = "\033[91m"  # For Errors
GREEN = "\033[92m"  # For received Acks
BLUE = "\033[94m"  # For finished sending all
PURPLE = "\033[95m"  # For start and end operations
CYAN = "\033[96m"  # For message that sent to the server
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

# --------------------------------------------------------------------------------------------------------------------------------------
""" We will access this function ONLY if the client chose to use the files!
Methods Goal:
    This function opens a file and reads its content. 
    we extract from it all the relevant fields we need such as: message,window_size and timeout
Returns:
    the field we exacted from the file, so the message,window_size and timeout
    """


def read_file(path):
    with open(path, 'r', encoding='utf-8') as file:
        for line in file:
            if line.startswith("message:"):
                message = line[9:len(line) - 2]
            else:
                x, data = line.rsplit(":", 1)
                if x == "window_size":
                    window_size = int(data)
                if x == "timeout":
                    time_out = int(data)
    return message, window_size, time_out


# --------------------------------------------------------------------------------------------------------------------------------------
"""
Methods Goal:
    to send the request to the server.
"""


def send_request_to_server(my_socket, request: str):
    try:
        my_socket.sendall((request.encode('utf-8')))
        print(f"{CYAN}Sent request: {request}{RESET}")
    except Exception as e:
        print(f"{RED}Error sending request: {e}{RESET}")


# --------------------------------------------------------------------------------------------------------------------------------------
"""
Methods Goal:
    to handle the ack messages of the server, we saved them in a list and returned it
"""


def handle_server_response(my_socket) -> list:
    try:
        response = my_socket.recv(1024)
        if response:
            decoded_response = response.decode('utf-8')
            messages = decoded_response.split("\\n")
            filtered_messages = []
            for message in messages:
                if message.startswith("ACK"):
                    filtered_messages.append(message)
            return filtered_messages
        else:
            return []
    except Exception:
        return []


# --------------------------------------------------------------------------------------------------------------------------------------
"""
Methods Goal:
    This function determines the number of digits in the input `number` by repeatedly dividing 
    it by 10 until it reaches 0.
Returns:
    The number of digits in the input number as an integer

"""


def cal_number_seg_size(number) -> int:
    count = 0
    x = int(number)
    while x != 0:
        count += 1
        x = x // 10
    return count


# --------------------------------------------------------------------------------------------------------------------------------------
"""
Methods Goal:
    This function splits the `message` into segments that do not exceed `max_size - 2` 
    Each segment is appended with an index in the format `:index`.
Returns: 
      A list of segmented message parts.
"""


def segment_message(message, max_size, window_size) -> list:
    segments = []
    x = 0
    start_index = 0
    num_of_digits = cal_number_seg_size(window_size + 10)
    end_index = max_size
    while start_index < len(message):
        seg_num = str(x % (window_size + 10))
        while len(seg_num) != num_of_digits:
            seg_num = "0" + seg_num
        s = message[start_index:end_index] + ":" + seg_num
        start_index = end_index
        x += 1
        end_index = end_index + max_size
        segments.append(s)
    return segments


# --------------------------------------------------------------------------------------------------------------------------------------
"""
Methods Goal:
    This function sends the segments to the server while maintaining a sliding window. It handles 
    acknowledgments and retransmissions in case of timeouts or unacknowledged segments.
Returns: 
      The function directly sends data over the socket and prints progress or errors.
"""


def sliding_window_send(my_socket, segments, window_size, timeout):
    num_segments = len(segments)
    acked = -1
    expected_ack = 0
    s = str(num_segments) + ":-1"
    send_request_to_server(my_socket, s)
    time.sleep(1)
    ack_list = handle_server_response(my_socket)
    while str(ack_list[0]) != "ACK-1":
        send_request_to_server(my_socket, s)
        time.sleep(1)
        ack_list = handle_server_response(my_socket)
    for i in range(0, min(window_size, num_segments)):
        send_request_to_server(my_socket, segments[i])
    while acked < num_segments - 1:
        start_time = time.time()
        while time.time() - start_time < timeout and acked < num_segments:
            ack_list = handle_server_response(my_socket)
            for ack in ack_list:
                ack_number = int(ack[3:])
                print(f"{GREEN}Acknowledgment received for segment {ack_number}{RESET}")
                if ack_number == expected_ack:
                    acked += 1
                    expected_ack = (expected_ack + 1) % (window_size + 10)
                    next_segment_index = acked + window_size
                    start_time = time.time()
                    if next_segment_index < num_segments:
                        send_request_to_server(my_socket, segments[next_segment_index])
            if acked + 1 == num_segments:
                break
        if time.time() - start_time >= timeout and acked < num_segments:
            print(f"{RED}Timeout occurred. Resending unacknowledged segments.txt.{RESET}")
            for i in range(acked + 1, min(acked + 1 + window_size, len(segments))):
                print(f"{YELLOW}Resending segment {segments[i]}{RESET}")
                send_request_to_server(my_socket, segments[i])


def handle_start(my_socket, window_size, is_from_file, path=""):

    decoded_response = 0
    print(f"{PURPLE}Connected to the server.{RESET}")
    if is_from_file:
        request = "max_file:" + path
        send_request_to_server(my_socket, request)
    else:
        request = "max"
        send_request_to_server(my_socket, request)
    try:
        response = my_socket.recv(1024)
        if response:
            decoded_response = response.decode('utf-8')
            print(f"{GREEN}Server maximum message size: {decoded_response}{RESET}")
    except Exception as e:
        print(f"{RED}Error receiving response: {e}{RESET}")
    request = "window size:" + str(window_size + 10)
    send_request_to_server(my_socket, request)
    try:
        response = my_socket.recv(1024)
        decoded_response2 = response.decode('utf-8')
        print(f"{GREEN}Accept for header: {decoded_response2}{RESET}")
    except Exception as e:
        print(f"{RED}Error receiving response: {e}{RESET}")
    if decoded_response and decoded_response.isdigit():
        max_size = int(decoded_response)
        return max_size
    else:
        print(f"{RED}Invalid response from server.{RESET}")
        return


# --------------------------------------------------------------------------------------------------------------------------------------

"""
Methods Goal:
    This function establishes a connection with a server, gets the maximum message size, 
    segments the message, and sends the segments using the sliding window protocol.

Returns: 
       The function directly communicates with the server and prints responses or errors.
"""


def client(message, window_size, timeout, is_from_file, path=""):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as my_socket:
            my_socket.settimeout(0.1)
            my_socket.connect((host, port))
            max_size = handle_start(my_socket, window_size, is_from_file, path)
            segments = segment_message(message, max_size, window_size)
            print(f"{PURPLE}Message segmented into {len(segments)} parts.{RESET}")
            try:
                sliding_window_send(my_socket, segments, window_size, timeout)
                time.sleep(1)
                response = my_socket.recv(1024)
                if response:
                    decoded_response = response.decode('utf-8')
                    print(f"{GREEN}Received response: {decoded_response}{RESET}")
            except Exception as e:
                print(f"{RED}Error receiving response: {e}{RESET}")
    except ConnectionRefusedError:
        print(f"{RED}Failed to connect to the server. Is it running?{RESET}")
    except Exception as e:
        print(f"{RED}An error occurred: {e}{RESET}")


# --------------------------------------------------------------------------------------------------------------------------------------
"""
in the main we had the clients input and direct him to the relevant path.
"""
if __name__ == '__main__':

    choice = input("Hello, you entered to selecting menu: \n\tPress 1 to read from a file\n\tPress 2 to write your "
                   "own message\nEnter key to continue:")
    if choice == "1":
        file_path = input("Enter the path to the file: ")
        msg, w_size, t_out = read_file(file_path)
        print(msg)
        print(w_size)
        print(t_out)
        client(msg, w_size, t_out, True, path=file_path)
    if choice == "2":
        msg = input("Enter the message to send: ")
        w_size = int(input("Enter the window size: "))
        t_out = int(input("Enter the timeout (in seconds): "))
        client(msg, w_size, t_out, False)
