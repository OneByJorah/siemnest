# Contributing

Thanks for helping. Small, focused changes get merged fastest.

## Run it locally

```bash
cp .env.example .env
docker compose up -d --build
```

The app listens on `http://127.0.0.1:8080`. Stop it with `docker compose down -v`.

## Workflow

1. Fork the repo and create a branch: `git checkout -b feat/short-description`.
2. Make your change and keep it focused on one thing.
3. Use [Conventional Commits](https://www.conventionalcommits.org/) for messages: `feat:`, `fix:`, `docs:`, `chore:`. Releases and the changelog are generated from them.
4. Run the checks you can locally: `docker build .`, `markdownlint-cli2 "**/*.md"`, `gitleaks detect`.
5. Open a pull request and fill in the template.

## Pull request checklist

- [ ] CI is green
- [ ] Docs and README updated if behaviour changed
- [ ] No secrets, hostnames, or real data in code, logs, or screenshots

## Reporting bugs and ideas

Use the issue templates. For security problems, see [SECURITY.md](SECURITY.md).
