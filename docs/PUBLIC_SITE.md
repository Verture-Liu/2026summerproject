# PaleoRigor public website

The public website is a static, English-language introduction to PaleoRigor. It explains the scientific problem, workflow, expert checkpoints, supported capability groups and measured validation evidence. It does not accept research data or execute bioinformatics Skills.

## Preview locally

From the repository root, run:

```bash
python3 -m http.server 8765 --directory docs
```

Then open <http://localhost:8765/>.

## Publish with GitHub Pages

1. Open the repository on GitHub.
2. Select **Settings → Pages**.
3. Under **Build and deployment**, choose **Deploy from a branch**.
4. Select branch **main** and folder **/docs**.
5. Save and wait for the Pages deployment to finish.

For this repository, the expected project-site address is:

<https://verture-liu.github.io/2026summerproject/>

The first deployment may take several minutes. The website uses project-relative asset paths so it works beneath the `/2026summerproject/` GitHub Pages subpath.

## Full local application

Real workflow planning and Skill execution remain in the local Python application. The public website links directly to the repository and the existing English installation guide.

