# Campus Event Notifier

**Find your people. Find your next campus event.**

Campus Event Notifier helps students at African universities discover and keep track of events taking place on campus.

## Problem statement

Across African university campuses, students often hear about activities through scattered chats, posters, and social media posts. Important events are easy to miss, especially for students who are new to campus or do not belong to the right groups. This application provides one simple place to publish and browse upcoming events. It is designed as a small, locally runnable foundation that a team can extend for the needs of its own campus.

## Target users

- University and college students looking for campus activities.
- Student clubs, societies, and event organizers sharing events.
- Campus community members who want a central event listing.

## Core features

- Create an event with a name, description, location, and date/time.
- View upcoming events ordered by start time.
- Validate event details before saving.
- Persist events locally in a JSON file across restarts.

## Technology stack

- **Language:** Python 3.10+
- **Server:** Python standard-library `http.server`
- **User interface:** HTML, CSS, and browser JavaScript
- **Data storage:** Local JSON file (no external services or runtime packages)
- **Testing:** Python `unittest`
- **Lint configuration:** Ruff settings in `pyproject.toml`
- **Deployment foundation:** Docker and GitHub Actions CI

The initial version deliberately uses a small HTTP server and a separate event-storage module. This keeps the feature easy to run for the formative while leaving clear boundaries for future deployment work. The development JSON file is not suitable for a multi-instance cloud deployment; a later iteration should use a shared database and a production-grade application server.

## Run locally

1. Install Python 3.10 or later. No third-party runtime packages are required.
2. From the project root, run:

   ```powershell
   python -m event_notifier
   ```

3. Open [http://127.0.0.1:8000](http://127.0.0.1:8000).
4. Add an event using the form. It is saved to `data/events.json`, which is generated when the first event is added.
5. Press `Ctrl+C` in the terminal to stop the server.

To select another port or data file:

```powershell
python -m event_notifier --port 8080 --data-file .\my-events.json
```

The server binds to `127.0.0.1` by default so it is only accessible from your computer. The JSON file is local development storage, not a production database.

## Run with Docker

Build and run the container from the project root:

```powershell
docker build -t campus-event-notifier .
docker run --rm -p 127.0.0.1:8000:8000 -v campus-events:/data campus-event-notifier
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The named Docker volume keeps event data between container runs. The container runs as a non-root user.

## Run tests

```powershell
python -m unittest discover -s tests -v
```

## Project structure

```text
event_notifier/
  __main__.py     Local server command and configuration
  events.py       Event validation, model, and JSON persistence
  index.html      Browser interface
  server.py       HTTP routes and JSON API
tests/
  test_events.py  Validation, persistence, and HTTP behavior tests
```

## GitHub and team setup checklist

The repository includes a GitHub Actions test workflow at `.github/workflows/ci.yml`. These remaining account-level tasks must be completed by the team in its GitHub repository:

- Create a GitHub Projects board using a Kanban view with **Backlog**, **In Progress**, and **Done** statuses.
- Seed the board with the following manageable items. Create a GitHub issue for each, add the indicated label and milestone, and assign a real team member:

  | Backlog item | Type / label | Milestone |
  | --- | --- | --- |
  | As a student, I want to search events by name so that I can find activities I care about. | Feature / `feature` | Formative 2 |
  | As a student, I want to filter events by date so that I can find events I can attend. | Feature / `feature` | Formative 2 |
  | As an organizer, I want to edit an event so that I can correct a listing after publishing it. | Feature / `feature` | Formative 2 |
  | As an organizer, I want to remove a cancelled event so that students do not rely on outdated information. | Feature / `feature` | Formative 2 |
  | Add tests for malformed JSON and event field length limits. | Testing / `testing` | Formative 2 |
  | Return a clear error when the saved event file is corrupted. | Bug / `bug` | Formative 2 |
  | Extend automated CI with linting and image checks. | DevOps / `devops` | Formative 2 |
  | Publish and deploy the Docker image to a cloud environment. | DevOps / `devops` | Formative 2 |
  | Replace local JSON storage with a shared database before multi-instance deployment. | DevOps / `devops` | Later formative |
  | Review request handling and document security decisions for the event API. | Security / `security` | Formative 2 |
  | Configure `main` branch protection and required checks after CI succeeds. | Security / `security` | Formative 1 |

  Agree on milestone dates with the course schedule. Add real assignees and move each issue between the required columns as work progresses; the items above are planning suggestions and are not GitHub issues until your team creates them.

- Add `feature`, `bug`, `devops`, and `security` labels and milestones aligned with the course deadlines.
- Enable Issues and Projects, then protect `main` with pull-request reviews, required checks, up-to-date branches, resolved conversations, stale-review dismissal, and administrator inclusion where supported by the repository plan.
- Use branches, pull requests, reviews, and meaningful commits with contributions from multiple team members. Select the required CI check after the workflow has run successfully.
- Have the team lead make a copy of the official [team participation sheet](https://docs.google.com/spreadsheets/d/1dWeSAKtChM3x1hGRWEio6HB32whUOYho8DuJwqFA1kc/copy), complete every section, and grant other members comment-only access.

This starter does not create GitHub issues, a project board, branch rules, team assignments, or a participation sheet. Add the actual repository and team details in GitHub/Google Sheets. The code being present locally also does not establish that it has been committed or that multiple team members have contributed; demonstrate those requirements in your repository's commit and pull-request history.
