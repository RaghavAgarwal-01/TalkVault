import os

dirs = [
    "infra/env",
    "infra/db",
    "docs/api",
    "api/app/core",
    "api/app/db/models",
    "api/app/db/migrations",
    "api/app/api/v1/endpoints",
    "api/app/api/v1/schemas",
    "api/app/api/v1/dependencies",
    "api/app/services",
    "api/app/middleware",
    "api/tests",
    "nlp/src/talkvault_nlp",
    "nlp/notebooks",
    "nlp/tests",
    "nlp/data/transcripts",
    "web/src/pages",
    "web/src/components",
    "web/src/lib",
    "web/src/styles",
    "web/public",
    "web/tests",
    "scripts"
]

for d in dirs:
    os.makedirs(d, exist_ok=True)
print("All directories created successfully.")
