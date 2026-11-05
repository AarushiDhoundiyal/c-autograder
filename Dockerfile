# AutoGrader image: pinned base, every analysis tool installed.
# The grader runs as root INSIDE the container only so that it can run every student program as the
# unprivileged user "nobody" while the hidden tests stay unreadable to that user (see agent/sandbox.py).
FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libc6-dev cppcheck valgrind \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV AUTOGRADER_DROP_PRIVILEGES=1
RUN chmod 755 /app \
    && chmod -R go-rwx /app/problems /app/rules /app/corpus /app/docs 2>/dev/null; true

# Command line:  docker run --rm --network none -v "$PWD/samples:/work" c-autograder \
#                    python grade.py /work/add_basic.c --rules rules/add_full.json
# Web app:       docker run -p 8000:8000 c-autograder sh -c \
#                    "python manage.py migrate && python manage.py seed_demo && python manage.py runserver 0.0.0.0:8000"
EXPOSE 8000
CMD ["python", "grade.py", "--help"]
