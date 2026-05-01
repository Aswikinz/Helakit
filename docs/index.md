---
hide:
  - navigation
  - toc
---

<div class="hk-hero" markdown>
<div class="hk-hero__copy" markdown>
<span class="hk-hero__tagline">Check it All</span>

# Validate Sri Lankan data, with confidence.

<p class="hk-hero__lede">
Helakit is a small, dependency-free Python library for validating and
parsing Sri Lankan identifiers — NIC numbers, phone numbers, postal
codes, and more. One result type, two entry points per validator,
zero runtime dependencies.
</p>

<div class="hk-hero__cta" markdown>
[Get started :material-arrow-right:](getting-started.md){ .md-button .md-button--primary }
[Validators](validators/nic.md){ .md-button }
[GitHub](https://github.com/Aswikinz/Helakit){ .md-button }
</div>
</div>

<div class="hk-hero__art">
<img src="assets/art/hero.svg" alt="Retro-futuristic illustration — placeholder until brand art is dropped in" />
</div>
</div>

## What's inside

```python
from helakit import validate_nic, is_valid_nic, convert_nic

result = validate_nic("820149894V")
result.data["decoded"].dob       # date(1982, 1, 14)
result.data["decoded"].gender    # "male"

is_valid_nic("199201409894")     # True
convert_nic("820149894V")        # "198201409894"
```

Pass a list, a `list[dict]`, a pandas DataFrame or a polars DataFrame
and the same call cross-checks every row against the supplied date of
birth and gender — flagging mismatches in detail.

## Validators

| Identifier | Status      | Reference                                  |
| ---------- | ----------- | ------------------------------------------ |
| NIC        | Available   | [NIC validator →](validators/nic.md)       |
| Phone      | Planned     | [Phone validator →](validators/phone.md)   |
| Postal     | Planned     | [Postal validator →](validators/postal.md) |
| Passport   | Planned     | —                                          |
| Vehicle    | Planned     | —                                          |

## Brand colours

The site uses the Helakit palette throughout. If you're integrating
helakit into a product, these are the tokens to reuse.

<div class="hk-swatches" markdown>
<div class="hk-swatch" style="--c: #20808d;"><span>Helakit Teal</span><code>#20808D</code></div>
<div class="hk-swatch" style="--c: #091717;"><span>Forest</span><code>#091717</code></div>
<div class="hk-swatch light" style="--c: #f8f4ec;"><span>Cream</span><code>#F8F4EC</code></div>
<div class="hk-swatch" style="--c: #3fb8c7;"><span>Teal Soft</span><code>#3FB8C7</code></div>
</div>

!!! warning "Alpha software"
    Helakit is pre-1.0. The public API may change before the first
    stable release; pin versions accordingly.
