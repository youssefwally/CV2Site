# CV2Site Static Website (code)

This folder contains a data-driven static site generated from a LaTeX CV. If you find my work useful for you, please keep the "Template Source github link in the footer". 

## Collaboration-first workflow

1. Update your source CV file (for example `CV/latex_tamplate.tex`).
2. Optionally configure parser overrides in `scripts/site-data.overrides.json`.
3. Regenerate `assets/js/site-data.js`.
4. Preview locally and commit.

## Generate site data

From the repository root:

```bash
python code/scripts/generate_site_data.py
```

This uses defaults:

- CV source: `CV/latex_tamplate.tex`
- Output: `code/assets/js/site-data.js`
- JS variable: `window.siteData`
- Overrides: `code/scripts/site-data.overrides.json`

Useful custom command:

```bash
python code/scripts/generate_site_data.py \
	--cv path/to/your-cv.tex \
	--output code/assets/js/site-data.js \
	--variable window.siteData \
	--overrides code/scripts/site-data.overrides.json
```

## Overrides example

Use `scripts/site-data.overrides.json` to customize extraction results without
editing Python code. The generator loads this file automatically when it exists.

What each key does:

- `publicationMetadata`: override URL, venue, status, and source links for specific publication titles.
- `venueAliases`: shorten long venue names (for example, expand full conference names into short labels).
- `authorNameMap`: map parsed surnames to your preferred full author names.
- `organizationLocationHints`: map organization keywords to locations used in the profile.
- `researchFallbackItems`: cards used when dynamic research cards cannot be generated.

Example `scripts/site-data.overrides.json`:

```json
{
	"publicationMetadata": {
		"Hyperbolic Graph Modeling for Biology": {
			"url": "https://doi.org/10.1000/example",
			"venue": "NeurIPS",
			"status": "Conference",
			"sources": [
				{
					"label": "ArXiv",
					"href": "https://arxiv.org/abs/2501.01234"
				},
				{
					"label": "Code",
					"href": "https://github.com/example/repo"
				}
			]
		}
	},
	"venueAliases": {
		"annual conference on neural information processing systems": "NeurIPS",
		"international conference on machine learning": "ICML"
	},
	"authorNameMap": {
		"smith": "Jane Smith",
		"doe": "John Doe"
	},
	"organizationLocationHints": {
		"university of oxford": "Oxford, United Kingdom",
		"massachusetts institute of technology": "Cambridge, United States"
	},
	"researchFallbackItems": [
		{
			"title": "Representation Learning",
			"description": "Methods for geometric and structure-aware representation learning."
		},
		{
			"title": "Applied AI",
			"description": "Applied machine learning for real-world scientific and product settings."
		},
		{
			"title": "Open Source and Community",
			"description": "Tooling, tutorials, and public contributions for collaborative research."
		}
	]
}
```

After updating the overrides file, regenerate data with:

```bash
python code/scripts/generate_site_data.py
```

## Project structure

- `index.html`: layout shell and section placeholders
- `assets/css/styles.css`: visual style and responsive behavior
- `assets/js/main.js`: rendering and browser interactions
- `assets/js/site-data.js`: generated content payload consumed by the page
- `scripts/generate_site_data.py`: LaTeX CV to website-data generator
- `scripts/site-data.overrides.json`: optional parser hints and metadata aliases



## Local preview

From the repository root:

```bash
npx serve code
```

Open the local URL printed by the command.

## To deploy on GitHub Pages:

1. Create a new repo: [your github username].github.io for a user page
2. On your repo go to settings->Pages then set choose "Source" as "Github Actions"
3. On your repo go to Actions->Deploy GitHub Pages->run workflow->run
4. Your website will be live at [your github username].github.io

## Security note

Everything under `code/` is public when deployed. Do not place private documents,
raw notes, or sensitive credentials in this folder.
