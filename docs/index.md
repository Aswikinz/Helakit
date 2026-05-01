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

<h2 class="hk-section-title">Validators</h2>

<div class="hk-validators" markdown>

<a class="hk-validator hk-validator--available" href="validators/nic/">
<span class="hk-validator__status">Available</span>
<span class="hk-validator__name">NIC</span>
<span class="hk-validator__desc">National Identity Card numbers — old (9 digits + V/X) and new (12 digit) formats, with cross-checking against supplied DOB and gender.</span>
</a>

<a class="hk-validator hk-validator--upcoming" href="validators/phone/">
<span class="hk-validator__status">Planned</span>
<span class="hk-validator__name">Phone</span>
<span class="hk-validator__desc">Sri Lankan phone numbers — mobile and fixed-line, with carrier and region detection.</span>
</a>

<a class="hk-validator hk-validator--upcoming" href="validators/postal/">
<span class="hk-validator__status">Planned</span>
<span class="hk-validator__name">Postal</span>
<span class="hk-validator__desc">Postal codes mapped to province, district and the nearest post office.</span>
</a>

<div class="hk-validator hk-validator--upcoming">
<span class="hk-validator__status">Planned</span>
<span class="hk-validator__name">Passport</span>
<span class="hk-validator__desc">Sri Lankan passport numbers, with type and issue-era detection.</span>
</div>

<div class="hk-validator hk-validator--upcoming">
<span class="hk-validator__status">Planned</span>
<span class="hk-validator__name">Vehicle</span>
<span class="hk-validator__desc">Vehicle registration numbers (cars, motorcycles, three-wheelers, lorries).</span>
</div>

</div>

!!! warning "Alpha software"
    Helakit is pre-1.0. The public API may change before the first
    stable release; pin versions accordingly.
