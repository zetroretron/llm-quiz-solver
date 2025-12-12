# Deployment Guide (Hugging Face Spaces)

This guide explains how to deploy your **LLM Analysis Quiz Solver** to **Hugging Face Spaces** (Free & Easy).

## Prerequisites

1.  **Hugging Face Account**: Sign up at [huggingface.co](https://huggingface.co/join).

---

## Deploy to Hugging Face Spaces

1.  **Create a New Space**:
    -   Go to [huggingface.co/new-space](https://huggingface.co/new-space).
    -   **Space Name**: `llm-analysis-quiz-solver` (or similar).
    -   **License**: `MIT`.
    -   **Select the Space SDK**: **Docker** (Crucial!).
    -   **Space Hardware**: **CPU Basic (Free)**.
    -   **Visibility**: **Public**.
    -   Click **Create Space**.

2.  **Upload Your Code**:
    -   You will see instructions to clone the repo, but the easiest way is to upload files directly in the browser.
    -   Go to the **Files** tab of your new Space.
    -   Click **Add file** -> **Upload files**.
    -   Drag and drop the following files from your computer:
        -   `Dockerfile`
        -   `requirements.txt`
        -   `main.py`
        -   `solver.py`
        -   `tools.py`
        -   `README.md`
    -   **Do NOT upload `.env`**.
    -   Click **Commit changes to main**.

3.  **Configure Secrets (API Keys)**:
    -   Go to the **Settings** tab of your Space.
    -   Scroll down to the **Variables and secrets** section.
    -   Click **New secret** (top right of that section).
    -   Add your secrets one by one:
        -   **Name**: `OPENAI_API_KEY`, **Value**: `sk-proj-...`
        -   **Name**: `STUDENT_SECRET`, **Value**: `your_secret_string`
    -   (Secrets are hidden and secure. The app reads them automatically).

4.  **Wait for Build**:
    -   Click on the **Logs** tab.
    -   You will see it building the Docker image. This takes a few minutes.
    -   Once it says "Running", your app is live!

5.  **Get Your API URL**:
    -   Click the **Embed this space** button (top right corner).
    -   Copy the **Direct URL**.
    -   It looks like: `https://username-space-name.hf.space`.
    -   **Your API Endpoint** is: `https://username-space-name.hf.space/run`

---

## Submission Details

When filling out the Google Form:

-   **API Endpoint URL**: `https://<username>-<space-name>.hf.space/run`
-   **GitHub Repo URL**: (If you created a separate GitHub repo, link it. If you are just using HF Spaces, you can link the Space URL, but the form asks for a GitHub repo. It is **highly recommended** to also push your code to a public GitHub repo as per the instructions).

    **To push to GitHub as well (Recommended):**
    1.  Create a public repo on GitHub.
    2.  Upload the same files there.
    3.  Submit that GitHub URL.

---

## Verification

To verify it's working:

1.  Open `test_local.py` locally.
2.  Change `API_URL` to your new Hugging Face URL:
    ```python
    API_URL = "https://<username>-<space-name>.hf.space"
    ```
3.  Run `python test_local.py`.
