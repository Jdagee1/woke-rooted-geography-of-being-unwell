# Publish Woke & Rooted to GitHub from Termius on your Ubuntu VM

The commands below **do not delete the VM database**. Use the **Add-on ZIP**, not the full repository ZIP, to update your already-working project.

## A. Transfer and safely merge the add-on

1. Download `Woke_Rooted_GitHub_Addon_v2.zip` to iPad Files.
2. Open Termius, connect to Ubuntu, and drag the ZIP into the Termius terminal. **Do not press Enter** on the bare `/tmp/...zip` path; a ZIP is not an executable program.
3. In Termius, list recent uploaded ZIPs to identify its actual path (Termius may rename the file to a UUID):

```bash
find /tmp "$HOME" -maxdepth 2 -type f -name '*.zip' -printf '%TY-%Tm-%Td %TH:%TM %p\n' 2>/dev/null | sort -r | head -15
```

4. Set `ZIP` to the **actual** file path returned. Example only; replace with your own actual path:

```bash
ZIP='/tmp/REPLACE_WITH_ACTUAL_UPLOADED_FILE.zip'
unzip -l "$ZIP" | head -35
unzip -t "$ZIP" | tail -1
```

Confirm the listing contains `README.md`, `sql/04_findings.sql`, and `docs/RESEARCH_MEMO.md`. If not, stop and inspect which file was selected.

5. Make a backup of your existing README *outside* the project and extract the add-on **into the project root** (not its parent folder):

```bash
cd ~/FM-Labs/Projects/Woke-Rooted/woke-rooted-mental-health-sql
cp README.md "$HOME/woke-rooted-README-before-publication.md"
unzip -o "$ZIP" -d "$PWD"
```

**Important:** The add-on contains **no** `src/pipeline.py`, raw CSV, database, or `.gitignore`. It will not overwrite the fix that made your CDC ingestion work, your original downloaded data, or your local Git configuration. It updates the README and results documentation and adds research materials. To protect your VM pipeline backup and secrets, add ignore rules:

```bash
printf '\n# Local work and secrets\n*.bak\n*.py.bak\n.env\n.env.*\ndata/*.download\n*.zip\n' >> .gitignore
```

## B. Verify code and findings *before* publishing

```bash
python3 -m py_compile src/pipeline.py src/generate_figures.py
python3 -m unittest discover -s tests -v
python3 src/pipeline.py --report
sqlite3 -header -column data/woke_rooted.sqlite < sql/04_findings.sql
python3 src/generate_figures.py
```

Compare your computed output with `docs/RESULTS.md`. Expected for the current 2024-release data: `3144` county records, `2417` complete cases, correlations close to `0.5069`, `0.4738`, `0.7180`. **If new output differs**, investigate before publishing; do not force-fit the numbers.

## C. Prepare the correct public files

Check that `git` exists (`git --version`). From the same project directory:

```bash
if [ -d .git ]; then
    echo 'Git repository already initialized'
else
    git init -b main
fi

git branch --show-current
git status --short
git check-ignore data/places_county_2024.csv data/woke_rooted.sqlite
```

`git check-ignore` should print both data filenames. If it does **not**, stop and correct `.gitignore` before staging. A missing `.gitignore` is a reason to stop. Check `git ls-files data/` to ensure a previous commit did not already track the raw data (ignored files that were already committed remain tracked).

Stage **only** the files intended for public GitHub. This deliberately excludes raw data and temporary backups:

```bash
git add README.md LICENSE .gitignore .github sql docs figures src/pipeline.py src/generate_figures.py tests/test_pipeline.py data/.gitkeep
git diff --cached --name-only
git diff --cached --stat
```

Check the staged list before committing. There should be no `.csv`, `.sqlite`, tokens, `.env`, backup `.bak`, or ZIP. If there are unintended files, unstage them with `git restore --staged PATH_TO_FILE` and inspect before continuing.

```bash
git commit -m "Publish Woke & Rooted CDC PLACES SQL research portfolio"
```

If Git asks you to configure an author, set **your own** preferred GitHub identity using `git config user.name` and `git config user.email` (you may use a GitHub no-reply email), then run the commit again.

## D. Create and upload to GitHub

**Preferred workflow on iPad + Ubuntu:** use GitHub CLI if available, because it can authenticate via a browser/device code.

```bash
gh --version || echo 'GitHub CLI not installed'
```

If needed and supported by your Ubuntu package sources: `sudo apt update && sudo apt install -y gh`.

```bash
gh auth login
```

Choose **GitHub.com**, **HTTPS**, and the **web browser/device login** option. Open the supplied GitHub device-login page on your iPad and enter the code displayed by Termius. Do **not** post the code, password, or token in chat or in the repository.

Then from your project directory run:

```bash
gh auth status
gh repo create woke-rooted-geography-of-being-unwell --public --source=. --remote=origin --push
```

This creates the public repository, sets `origin`, and pushes the local commit. If the repository already exists, don't run `gh repo create` again. Instead inspect `git remote -v` and use `git push -u origin main` once `origin` points to the **correct** GitHub repo and the current branch is `main`.

**Alternative: GitHub website + Git commands.** On your iPad, create an **empty** public repo on GitHub named `woke-rooted-geography-of-being-unwell`. Do not add a README, `.gitignore`, or license via the website, because these files already exist locally. In Termius:

```bash
git remote add origin https://github.com/YOUR_USERNAME/woke-rooted-geography-of-being-unwell.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username; if `origin` already exists, inspect `git remote -v` instead of adding it twice. Password-based Git HTTPS authentication is not supported: use GitHub CLI browser authentication or a GitHub personal access token when prompted. Do not place tokens directly inside remote URLs or shell commands.

## E. Verify that publishing worked

```bash
git status -sb
git remote -v
git log -1 --oneline
```

Open the new GitHub repository in a browser and verify these visible paths:

- `README.md` with the correlation heatmap preview
- `sql/04_findings.sql`
- `docs/RESULTS.md`
- `docs/RESEARCH_MEMO.md`
- `docs/WOKE_ROOTED_ARTICLE_DRAFT.md`
- `figures/correlation_heatmap.png`
- `figures/scatter_isolation_distress.svg` (generated on the VM)
- `.github/workflows/tests.yml` and a successful Actions test run

The public GitHub repository is your **code + documented research**, not a database backup. Keep the raw CSV and SQLite on your VM, backed up separately to a secure location. GitHub also warns users not to commit credentials or secrets.

**GitHub reference:** https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github
