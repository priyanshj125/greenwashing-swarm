"""
Ground Truth Vector Store — SBTi & Industry Benchmark Seed Data
Populated into ChromaDB on first backend startup.
"""

BENCHMARK_DOCUMENTS = [
    # ── Science Based Targets initiative (SBTi) ─────────────────────────────
    {
        "id": "sbti-001",
        "text": (
            "The Science Based Targets initiative (SBTi) requires companies to reduce "
            "Scope 1 and 2 emissions by 4.2% per year to align with a 1.5°C pathway. "
            "Far-reaching claims of 'carbon neutrality' without offsetting Scope 3 "
            "do not meet SBTi Net-Zero Standard criteria."
        ),
        "metadata": {
            "source": "SBTi Net-Zero Standard v1.0",
            "category": "carbon",
            "source_url": "https://sciencebasedtargets.org/net-zero",
        },
    },
    {
        "id": "sbti-002",
        "text": (
            "SBTi defines 'carbon neutrality' as achieving a state where an organization's "
            "net greenhouse gas impact is zero by balancing measured, verified emissions with "
            "certified carbon removals. Marketing claims of 'carbon neutral' that rely solely "
            "on voluntary carbon offsets (without verification) are considered misleading under "
            "SBTi standards."
        ),
        "metadata": {
            "source": "SBTi Corporate Net-Zero Standard",
            "category": "net_zero",
            "source_url": "https://sciencebasedtargets.org/resources/files/Net-Zero-Standard.pdf",
        },
    },
    # ── CDP Sector Averages ───────────────────────────────────────────────────
    {
        "id": "cdp-001",
        "text": (
            "CDP 2023 data: The global average Scope 1 emission reduction rate across "
            "Fortune 500 companies was 3.1% year-over-year. Claims of reductions exceeding "
            "15% in a single year without capital expenditure evidence are statistical outliers "
            "that warrant independent verification."
        ),
        "metadata": {
            "source": "CDP Global Corporate Environmental Report 2023",
            "category": "carbon",
            "source_url": "https://www.cdp.net/en/research/global-reports",
        },
    },
    {
        "id": "cdp-002",
        "text": (
            "CDP data indicates that only 1 in 200 companies globally has achieved verified "
            "100% renewable electricity sourcing (RE100). Claims of '100% renewable energy' "
            "require documentation of Power Purchase Agreements (PPAs) or Renewable Energy "
            "Certificates (RECs) to be credible."
        ),
        "metadata": {
            "source": "CDP & RE100 Annual Progress Report 2023",
            "category": "renewable",
            "source_url": "https://www.cdp.net/en",
        },
    },
    # ── IPCC Benchmarks ───────────────────────────────────────────────────────
    {
        "id": "ipcc-001",
        "text": (
            "IPCC AR6 (2022): Global emissions must fall by 43% by 2030 relative to 2019 "
            "levels to limit warming to 1.5°C. Corporate net-zero claims that target 2050 "
            "without interim 2030 milestones are inconsistent with IPCC urgency timelines."
        ),
        "metadata": {
            "source": "IPCC Sixth Assessment Report AR6 — Mitigation",
            "category": "carbon",
            "source_url": "https://www.ipcc.ch/report/ar6/wg3/",
        },
    },
    # ── GHG Protocol ─────────────────────────────────────────────────────────
    {
        "id": "ghgp-001",
        "text": (
            "The GHG Protocol Corporate Standard requires companies reporting Scope 3 "
            "emissions to cover at least the categories relevant to their business. "
            "A company claiming to be 'climate positive' while omitting Scope 3 supply chain "
            "emissions (typically 70-90% of total footprint for consumer-facing companies) "
            "does not meet GHG Protocol completeness requirements."
        ),
        "metadata": {
            "source": "GHG Protocol Corporate Standard",
            "category": "carbon",
            "source_url": "https://ghgprotocol.org/corporate-standard",
        },
    },
    # ── Water Stewardship ─────────────────────────────────────────────────────
    {
        "id": "aws-001",
        "text": (
            "Alliance for Water Stewardship (AWS) Standard: Claims of 'water positive' or "
            "'water neutral' require site-level water accounting verified against local "
            "watershed baselines. Company-wide statements about water stewardship without "
            "facility-specific data do not meet AWS Standard requirements."
        ),
        "metadata": {
            "source": "AWS International Water Stewardship Standard v2.0",
            "category": "water",
            "source_url": "https://a4ws.org/the-aws-standard/",
        },
    },
    # ── Social / Supply Chain ─────────────────────────────────────────────────
    {
        "id": "ungp-001",
        "text": (
            "UN Guiding Principles on Business and Human Rights (UNGPs) state that companies "
            "must conduct ongoing human rights due diligence across their supply chains. "
            "Claims of 'responsible sourcing' or 'ethical supply chains' without published "
            "supplier audit results or third-party verification are not compliant with UNGP expectations."
        ),
        "metadata": {
            "source": "UN Guiding Principles on Business and Human Rights",
            "category": "supply_chain",
            "source_url": "https://www.unglobalcompact.org/what-is-gc/our-work/social/human-rights",
        },
    },
]
