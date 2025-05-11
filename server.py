import socket
import threading
import time
import csv

# host is left empty so it accepts connections from any IP
HOST = ''
PORT = 12345

# to keep track of IPs that already submitted
connected_ips = set()

# to store each client's roll number and their answers
clients_data = {}

# to store scores for each roll number
scores = {}

# questions for the quiz
single_correct_questions = [
    ("What does IP stand for?\nA. Internet Protocol\nB. Internal Process\nC. Interconnected Packet\nD. Input Protocol", "A"),
    ("Which device operates at Layer 2 of the OSI model?\nA. Router\nB. Switch\nC. Hub\nD. Modem", "B"),
    ("What is the default port number for HTTP?\nA. 80\nB. 21\nC. 23\nD. 110", "A"),
    ("Which layer is responsible for end-to-end communication?\nA. Network\nB. Transport\nC. Application\nD. Data Link", "B"),
    ("Which protocol is used to send email?\nA. FTP\nB. SMTP\nC. POP3\nD. IMAP", "B")
]

multiple_correct_questions = [
    ("Which of the following are transport layer protocols?\nA. TCP\nB. UDP\nC. IP\nD. HTTP", ["A", "B"]),
    ("Which are valid IP address classes?\nA. Class A\nB. Class B\nC. Class E\nD. Class G", ["A", "B", "C"]),
    ("Which of the following are application layer protocols?\nA. FTP\nB. DNS\nC. TCP\nD. HTTP", ["A", "B", "D"]),
    ("Which protocols use port number 443 or 80?\nA. HTTPS\nB. HTTP\nC. SSH\nD. TELNET", ["A", "B"])
]

single_word_questions = [
    ("What is the full form of DNS?", "Domain Name System"),
    ("Which device connects different networks together?", "Router")
]

# marks for each type of question
marks_single = 2
marks_multiple = 4
marks_word = 3

# function that handles one client at a time
def handle_client(conn, addr):
    ip = addr[0]
    print(f"Connection from {ip}")

    # receive the roll number from client
    roll = conn.recv(1024).decode().strip()

    # check if roll number is valid and in allowed range
    if not (roll.isdigit() and 2303101 <= int(roll) <= 2303140):
        conn.sendall("Your roll number is not authorized.".encode())
        conn.close()
        return

    # if roll number already submitted
    if roll in scores:
        conn.sendall("Your roll number has already given answers and you cannot give now.".encode())
        conn.close()
        return

    # if IP already submitted
    if ip in connected_ips:
        conn.sendall("Your IP has already given answers and you cannot give now.".encode())
        conn.close()
        return

    # add IP to the submitted list
    connected_ips.add(ip)
    # store roll and empty answer list
    clients_data[ip] = {'roll': roll, 'answers': []}

    # tell client quiz is starting
    conn.sendall("You are authorized. Quiz starting now.".encode())

    score = 0  # to store the total score of the client

    # handle single correct questions
    for q, a in single_correct_questions:
        conn.sendall(q.encode())
        answer = conn.recv(1024).decode().strip().upper()
        clients_data[ip]['answers'].append(answer)
        if answer == a:
            score += marks_single

    # handle multiple correct questions
    for q, a in multiple_correct_questions:
        conn.sendall(q.encode())
        answer = conn.recv(1024).decode().strip().upper().split()
        clients_data[ip]['answers'].append(' '.join(answer))
        if sorted(answer) == sorted(a):
            score += marks_multiple

    # handle single word questions
    for q, a in single_word_questions:
        conn.sendall(q.encode())
        answer = conn.recv(1024).decode().strip()
        clients_data[ip]['answers'].append(answer)
        if answer.lower() == a.lower():
            score += marks_word

    # save the final score of the roll number
    scores[roll] = score

    # tell client their final score
    conn.sendall(f"Thank you. Your score: {score}".encode())
    conn.close()

# function to save all data once server is closed
def save_results():
    # saving answers to csv file
    with open("answers.csv", "w", newline='') as f:
        writer = csv.writer(f)
        headers = ['Roll No', 'IP'] + [f"Q{i+1}" for i in range(len(single_correct_questions + multiple_correct_questions + single_word_questions))]
        writer.writerow(headers)
        for ip, data in clients_data.items():
            writer.writerow([data['roll'], ip] + data['answers'])

    # saving leaderboard in descending order
    with open("leaderboard.txt", "w") as f:
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        for roll, score in sorted_scores:
            f.write(f"{roll}: {score}\n")

    # creating question and answer list
    question_texts = (
        [q for q, _ in single_correct_questions] +
        [q for q, _ in multiple_correct_questions] +
        [q for q, _ in single_word_questions]
    )
    correct_answers = (
        [a for _, a in single_correct_questions] +
        [a for _, a in multiple_correct_questions] +
        [a for _, a in single_word_questions]
    )

    total_questions = len(question_texts)
    correct_counts = [0] * total_questions
    total_attempts = len(clients_data)

    # count how many people answered each question correctly
    for data in clients_data.values():
        answers = data['answers']
        for i, ans in enumerate(answers):
            correct = correct_answers[i]
            if isinstance(correct, list):
                given = sorted(ans.strip().split())
                if given == sorted(correct):
                    correct_counts[i] += 1
            else:
                if str(ans).strip().lower() == str(correct).strip().lower():
                    correct_counts[i] += 1

    # save analysis of each question in a text file
    with open("analysis.txt", "w") as f:
        for i in range(total_questions):
            f.write(f"Q{i+1}: {question_texts[i].splitlines()[0]}\n")
            f.write(f"Correct Answers: {correct_answers[i]}\n")
            f.write(f"Correct Count: {correct_counts[i]}/{total_attempts} ({(correct_counts[i]/total_attempts)*100:.2f}%)\n\n")

# main function that starts the server
def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Server started on port {PORT}")

    try:
        while True:
            conn, addr = server.accept()
            # create a thread for every new client connection
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\nShutting down server and saving results...")
        save_results()
        server.close()

# run the server
if __name__ == "__main__":
    main()
