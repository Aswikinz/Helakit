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
<img src="assets/art/2.png" alt="Helakit — Know it all, Check it All" />
</div>
</div>

<div class="hk-feature" markdown>
<span class="hk-feature__badge">Available now</span>
<h2 class="hk-feature__name">NIC validator</h2>
<p class="hk-feature__desc">
Validate Sri Lankan National Identity Cards in either format — the old
9 digits + V/X or the new 12-digit numeric — and decode birth date,
gender, and voting eligibility. Cross-check supplied DOB and gender
against the encoded values across single strings, lists, pandas
DataFrames or polars DataFrames.
</p>

[Read the NIC docs :material-arrow-right:](validators/nic.md){ .md-button .md-button--primary }
</div>

<div class="hk-roadmap" markdown>
<span class="hk-roadmap__label">On the roadmap</span>
<a class="hk-roadmap__item" href="validators/phone.md">Phone</a>
<a class="hk-roadmap__item" href="validators/postal.md">Postal</a>
<span class="hk-roadmap__item">Passport</span>
</div>

!!! warning "Alpha software"
    Helakit is pre-1.0. The public API may change before the first
    stable release; pin versions accordingly.
