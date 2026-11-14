# 📘 How to upload MedAI Hub to GitHub and share the link

This guide assumes you have **never used GitHub**. Follow the steps in order. Total time: about 20 minutes.

---

## Step 0 - Unzip the project
Right-click the downloaded `medai-hub.zip` → **Extract All** (Windows) / double-click (Mac). You should get a folder called `medai-hub` that contains `app.py`, `README.md`, etc.

**Test it first** (so your teacher's link opens a working project):
```bash
cd medai-hub
python -m venv venv
venv\Scripts\activate        # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python app.py                # open http://127.0.0.1:5000
```

---

## Step 1 - Create a GitHub account
1. Go to **https://github.com** → **Sign up**.
2. Choose a *professional* username (e.g. `mohammed-faraz`) - it will appear in the link your teacher shares in the Germany application.
3. Verify your email.

## Step 2 - Install Git
* Download from **https://git-scm.com/downloads** and install with default options.
* Open **Git Bash** (Windows) or Terminal (Mac/Linux) and check: `git --version`
* Tell Git who you are (use the same email as your GitHub account):
```bash
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

## Step 3 - Create an empty repository on GitHub
1. Click the **+** (top-right) → **New repository**.
2. **Repository name:** `medai-hub`
3. **Description:** `Medical Diagnosis System using AI and Machine Learning - Flask web app`
4. Choose **Public** (so your teacher and the university can open it without logging in).
5. **Do NOT** tick "Add a README", ".gitignore" or "license" - the project already has them.
6. Click **Create repository**. Keep this page open.

## Step 4 - Upload your project (choose ONE method)

### Method A - Command line (recommended, 2 minutes)
In Git Bash / Terminal, go **inside the project folder** and run:
```bash
cd path/to/medai-hub
git init
git add .
git commit -m "Initial commit: MedAI Hub medical diagnosis system"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/medai-hub.git
git push -u origin main
```
(Replace `YOUR-USERNAME`.) When asked to log in:
* A browser window usually opens - just sign in. 
* If it asks for a **password**, GitHub no longer accepts your account password. Create a token: GitHub → profile picture → **Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token**, tick **repo**, copy it, and paste it as the password.

### Method B - GitHub Desktop (no commands)
1. Install **GitHub Desktop** from https://desktop.github.com and sign in.
2. **File → Add local repository** → choose the `medai-hub` folder (click "create a repository" if it asks).
3. Write a summary ("Initial commit") → **Commit to main** → **Publish repository** → untick "Keep this code private" → **Publish**.

### Method C - Drag and drop in the browser (last resort)
On your empty repo page click **uploading an existing file**, drag the *contents* of the `medai-hub` folder in, wait for upload, then **Commit changes**. (Keeps folders, but the upload limit is 100 files per batch - this project is under that.)

## Step 5 - Check it
Open `https://github.com/YOUR-USERNAME/medai-hub`. You should see the README with the screenshots rendered, and the folders `ml`, `templates`, `static`, `tests`.

## Step 6 - Make the repository look professional
* On the repo page click the ⚙️ next to **About** → add the description and **Topics**: `machine-learning`, `flask`, `healthcare`, `python`, `scikit-learn`, `ai`.
* In `README.md`, replace `<your-username>` in the clone command with your real username (click the ✏️ pencil icon → edit → **Commit changes**).
* Add your teammates: **Settings → Collaborators → Add people**.
* Keep the **Limitations** section in the README. Admissions committees and professors value honesty about what the project does and doesn't do.

## Step 7 - Share the link with your teacher
Send this exact link (copy it from the browser address bar):

```
https://github.com/YOUR-USERNAME/medai-hub
```

Suggested message:
> Respected Sir/Madam, here is our final-year project repository: https://github.com/YOUR-USERNAME/medai-hub - the README explains the features, how to run it, and the tests. Thank you.

Open the link in a **private/incognito window** to confirm it works without logging in.

---

## Updating the project later
After changing files:
```bash
git add .
git commit -m "Describe what you changed"
git push
```

## 🌐 Optional: put it online (live demo link)
A running website impresses reviewers more than code alone. Free option: **Render.com**
1. Sign in with GitHub → **New → Web Service** → pick `medai-hub`.
2. Build command: `pip install -r requirements.txt` · Start command: `gunicorn app:app`
3. Add an environment variable `SECRET_KEY` with any long random text.
4. Deploy. The free tier "sleeps" when idle, so the first load can take ~1 minute.
5. Add the live URL to your README.

Note: on free hosting, user accounts/history stored in SQLite may be reset on restart - fine for a demo.

## ❓ Common problems
| Problem | Fix |
|---|---|
| `git is not recognized` | Reinstall Git, then reopen the terminal |
| `failed to push… authentication` | Use a Personal Access Token as the password (Step 4A) |
| `remote origin already exists` | `git remote set-url origin https://github.com/YOUR-USERNAME/medai-hub.git` |
| `src refspec main does not match` | Run `git add .` and `git commit` first, then push |
| README images not showing | Make sure the `static/img/report/` folder was uploaded |
