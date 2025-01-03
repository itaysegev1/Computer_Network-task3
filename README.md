# TCP Connection: Client-Server

This project implements a client-server architecture for reliable message transfer using TCP sockets. It ensures message segmentation, order maintenance, acknowledgment handling, and retransmission in case of failures.

---

## Features

### 1. **Client-Server Communication**
- Clients send messages of various lengths to the server.
- The server reassembles messages from multiple segments to recreate the complete message.
- The server sends confirmation upon successfully receiving all segments.

### 2. **Sliding Window Protocol**
- Enables efficient and reliable transfer of message segments.
- Handles acknowledgments and retransmissions for unacknowledged segments.
- Advances dynamically based on received acknowledgments.

### 3. **Dynamic Message Size**
- Supports configuration of the server's maximum message size.
- Dynamically adjusts based on server or file configuration.

### 4. **File Integration**
- Allows clients to load configurations (message, window size, timeout) from files.
- Provides an option for clients to use file-based or manual configurations.

### 5. **Error Handling**
- Manages out-of-order message segments.
- Implements timeout mechanisms and retransmissions.
- Uses default values for invalid user inputs.
- Handles file-related errors (e.g., file not found).

### 6. **Colors**
- There are differnt colors for the message of the client and the messages of the server
- All the errors and problems will be printed in red

---

## File Structure

### 1. `client.py`
- **Client-Side Logic**:
  - Reads configurations from files or user input.
  - Handles input errors by falling back to default values.
  - Segments messages into smaller parts based on the server's maximum message size.
  - Implements the sliding window protocol for sending message segments.

### 2. `server.py`
- **Server-Side Logic**:
  - Processes client requests and maintains connection state.
  - Reorders and combines received message segments.
  - Sends acknowledgments to clients and retransmits missing segments.
  - Utilizes a buffer to handle out-of-order segments.

---

## Getting Started

### Prerequisites
- Compatible with Linux (Ubuntu), Windows, and macOS (Silicon).
- Ensure the configuration file follows this structure:
  ```
  message: "<your_message_here>" (A string enclosed in quotation marks)
  maximum_msg_size: "<max_bytes>" (A string representing the number of bytes as an integer)
  window_size: "<window_size>" (A string representing the number of messages in a window as an integer)
  timeout: "<timeout>" (A string representing the timeout in seconds as an integer)
  ```
- The file content must be UTF-8 encoded and contain only ASCII characters.
- All files should reside in the same directory.
- You can add new files of your own, the project become with 2 Files

### Debugging Options
- **Drop Segments**: Enable this feature in the `server.py` by modifying the `client-handler` method.
- **Out-of-Order Segments**: Enable this feature in the `client.py` by modifying the `client` method.

---

## Usage

1. **Start the Server and Client**:
   - Launch the server application first.
   - Follow by starting the client application.

2. **Server Configuration**:
   - Choose whether to manually specify the maximum segment size.
   - If manual input is selected and the client uses a file, the server will adopt the file’s maximum segment size.

3. **Client Configuration**:
   - Choose one of the following options:
     - **Option 1**: Enter the file path to load configurations.
     - **Option 2**: Manually enter all configurations (message, window size, timeout).

4. **File-Based Configuration**:
   - If a file is used, the client automatically loads the configurations and begins transmission.

5. **Manual Configuration**:
   - Enter the message and other parameters as prompted.

---

This setup ensures robust and reliable communication between client and server while allowing flexibility for debugging and customization.

