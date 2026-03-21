# mainsite

## CSS Workflow

Readable source CSS lives in `styles/*.css`.

### Commands

- Build minified CSS files:
  - `make css-build`
- Switch HTML pages to production CSS links (`.min.css`):
  - `make css-prod`
- Switch HTML pages back to readable CSS links (`.css`):
  - `make css-dev`
- Check current link mode:
  - `make css-status`

### Notes

- `css-prod` always rebuilds minified files before switching links.
- Minified files are generated next to source files, e.g.:
  - `styles/index.css` -> `styles/index.min.css`
  - `styles/common.css` -> `styles/common.min.css`
