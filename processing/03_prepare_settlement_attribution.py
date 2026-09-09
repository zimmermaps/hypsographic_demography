"""Record the GHS-SMOD settlement attribution used upstream.

The main figures use static_2025 attribution for settlement-specific growth.
Dynamic attribution is retained only as a comparison diagnostic.
"""


SETTLEMENT_CLASSES = [
    "Low-density rural",
    "Rural cluster",
    "Peri-urban",
    "Semi-dense urban",
    "Dense urban",
    "Urban centre",
]


def main() -> None:
    notes = """
    Upstream workflow:
    1. Align GHS-SMOD R2023A classes to the WorldPop grid.
    2. Use nearest-neighbor resampling for settlement classes.
    3. Build static_2025 attribution by applying 2025 classes to all years.
    4. Build dynamic attribution by using the class associated with each year.
    5. Exclude Unknown/water classes from the final settlement matrix.
    """
    print(notes.strip())


if __name__ == "__main__":
    main()
