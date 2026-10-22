# Private preview

A locked, view-only preview. Nothing readable is in this repo: each person's copy in `copies/<ID>.json` is encrypted with that person's own access code, and `index.html` is the terms and code page that opens it in the browser.

- Link for a copy: `https://andrew-hap.github.io/nc-preview/?c=<ID>`
- The page fetches the copy fresh on every open (GitHub Pages caches files for 10 minutes), so updates show at once.
- Switch a copy off: delete `copies/<ID>.json`, commit, push.
- Expiry, watermark (with the copy ID), view-only blocks and the terms gate come from `protect.html` and `gate.html`. `mobile-patch.html` makes the header scroll away on phones, with a slim bar on scroll up.
- The register of who holds which code is kept outside this repo.

Rebuild after a new export from the design tool: the content-change scripts are kept privately,
outside this public repo, because they quote the text they replace. Run them first, then:

```
python3 issue.py <changed page>.html <expires YYYY-MM-DD> <ID>=<who>[|<code>[|general]] ...
```

Then commit and push `index.html` and `copies/`.
