# Site artwork

Drop your retro-futuristic art into this folder. The site references a
fixed set of filenames — replace each placeholder with your own image
and the page picks it up automatically. Recommended format is `.webp`
or `.jpg` for photographic / painterly art (small file size); use
`.svg` only for line-art or geometric pieces.

## Where each file shows up

| File                       | Where it appears                                                                | Recommended size / aspect              |
| -------------------------- | ------------------------------------------------------------------------------- | -------------------------------------- |
| `hero.webp`                | The big square slot on the homepage hero, opposite the headline.                | 1:1 square, ~1200px on the long edge   |
| `validators-nic.webp`      | Top of [`docs/validators/nic.md`](../../validators/nic.md) when wrapped in `<div class="hk-decoration">`. | 16:6 banner, ~1600x600     |
| `validators-phone.webp`    | Top of the Phone validator page (when added).                                   | 16:6 banner                            |
| `validators-postal.webp`   | Top of the Postal validator page (when added).                                  | 16:6 banner                            |
| `getting-started.webp`     | Hero on the Getting Started page.                                               | 16:9 banner, ~1600x900                 |
| `og-card.png`              | Open Graph / Twitter share image (used by mkdocs-material if enabled).          | 1200x630 PNG (social-card spec)        |

If you change file extensions (e.g. drop `.jpg` instead of `.webp`),
update the corresponding `<img src=...>` reference in the markdown
page. The hero on the homepage is wired up in
[`docs/index.md`](../../index.md).

## Style direction

The brand kit calls for a retro-futuristic / pulp-illustrative
aesthetic — think the page-3 illustration in `helakit-brandkit.pdf`.
Recurring cues from the brand kit:

- Saturated sunset oranges / lavenders against deep blues
- Stippled / grainy texture
- Mountain or horizon silhouettes
- A solitary figure looking outward (optional, but on-brand)
- Stars / cosmic flourishes

When in doubt, lean toward **warm sunset over cool night sky**, framed
by silhouetted forms. The teal accent (`#20808D`) reads well as a
glow / aurora highlight inside that palette.

## Placeholders

`hero.svg` is a minimal placeholder so the homepage doesn't show a
broken image before you ship real art. Once you drop in `hero.webp`
(or any other extension), update the homepage `<img>` reference and
delete the placeholder.

## Not tracked yet?

If you'd like contributors to commit artwork, leave this folder under
git. If artwork is heavy / generated separately, add `docs/assets/art/`
to [`.gitignore`](../../../.gitignore) and treat it like the
`notebooks/` folder — local-only.
