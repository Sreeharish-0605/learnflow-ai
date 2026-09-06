from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import LearningPath, Task

PATHS = [
    ("Cloud & OCI", "Learn core cloud concepts and deploy your first secure OCI application.", [
        ("Understand cloud basics", "Learn IaaS, PaaS, SaaS and regions.", "https://www.oracle.com/cloud/"),
        ("Create an OCI VCN", "Create a VCN, a public subnet and a security rule for your app.", None),
        ("Deploy a Compute VM", "Launch a Linux VM and connect securely using SSH.", None),
        ("Learn Object Storage", "Create a bucket and understand buckets, objects and access rules.", None),
        ("Explore Autonomous Database", "Create a free database and run your first SQL queries.", None),
    ]),
    ("Python Backend", "Build APIs, databases, authentication and deployment skills.", [
        ("Python fundamentals", "Practice functions, lists, dictionaries and error handling.", "https://docs.python.org/3/tutorial/"),
        ("Build a FastAPI endpoint", "Create a GET endpoint and test it in the browser.", "https://fastapi.tiangolo.com/"),
        ("Learn SQL basics", "Write SELECT, INSERT, UPDATE and JOIN queries.", None),
        ("Add authentication", "Understand password hashing and sessions.", None),
        ("Dockerize an app", "Build and run your application in a Docker container.", None),
    ]),
    ("SQL & Data", "Build practical database and data-analysis foundations.", [
        ("Design a table", "Learn primary keys, foreign keys and normalisation.", None),
        ("Write SELECT queries", "Filter, sort and aggregate a data set.", None),
        ("Use JOINs", "Combine users, tasks and progress data.", None),
        ("Create an index", "Learn why indexes make frequent queries faster.", None),
        ("Build a dashboard query", "Calculate completion percentage per user.", None),
    ]),
]


def seed_database(db: Session) -> None:
    if db.scalar(select(LearningPath.id).limit(1)):
        return
    for title, description, tasks in PATHS:
        path = LearningPath(title=title, description=description)
        db.add(path)
        db.flush()
        for position, (task_title, task_description, resource_url) in enumerate(tasks, 1):
            db.add(Task(path_id=path.id, title=task_title, description=task_description,
                        resource_url=resource_url, position=position))
    db.commit()
