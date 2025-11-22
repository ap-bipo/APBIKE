import os

def send_email():
    with open("email.txt", "w") as f:
        f.write("""To: cudemlmao@gmail.com
From: yourgmail@gmail.com
Subject:

Nguoi than khiem thi cua ban dang gap nguy hiem hay kiem tra ngay !!!
""")
    os.system("ssmtp cudemlmao@gmail.com < email.txt")

send_email()
