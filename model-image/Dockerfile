FROM python:latest
WORKDIR /application

# RUN sudo apt install pkg-config 

# MAY HAVE TO DOWNLOAD A BUNCH OF SHIT, PLEASE SEE: https://itslinuxfoss.com/fix-command-x86-64-linux-gnu-gcc-failed-with-exit-status1/

# ALSO DOWNLOAD: https://stackoverflow.com/questions/23937933/could-not-run-curl-config-errno-2-no-such-file-or-directory-when-installing

# MAKE SURE TO ALSO DOWNLOAD GCC compiler

COPY app app
COPY run_app.sh run_app.sh
COPY requirements.txt requirements.txt

RUN pip install -no-cache-dir -r requirements.txt
RUN chmod +x /application/run_app.sh

ENTRYPOINT [ "/application/run_app.sh" ]

