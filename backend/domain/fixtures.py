from random import Random

WINDOWS = (
    ("WIN-ARC", "河埠拱角橱窗", "FROST-03", 1170, 1440, 95, 70, 20, "vertical", True),
    ("WIN-LANE", "北巷书店直窗", "FROST-03", 930, 1300, 10, 15, 20, "vertical", False),
    ("WIN-LETTER", "字画铺横窗", "FROST-03", 1290, 680, 20, 25, 15, "any", False),
)
ROLLS = (
    ("ROLL-A12", "FROST-03", 1220, 20, "lengthwise", 105, 15000),
    ("ROLL-NAR", "FROST-03", 530, 15, "lengthwise", 100, 6000),
    ("ROLL-END", "FROST-03", 1220, 20, "lengthwise", 110, 2050),
    ("ROLL-NEU", "FROST-03", 1120, 10, "neutral", 98, 11000),
)


def historical_scraps():
    generator = Random(20201125)
    for i in range(216):
        panels = 1 + i % 2
        feed = generator.randrange(300, 10501, 100)
        usable = generator.randrange(180, 3501, 20)
        across = generator.randint(150, usable)
        bevel = generator.randrange(0, 801, 10)
        thickness = generator.randint(30, 300)
        loss = round(
            11 + 0.019 * feed + 0.18 * bevel + 14 * panels + thickness / 13
            + 35 * (across / usable > 0.87) + generator.gauss(0, 14)
        )
        yield (f"HIST-{i:03d}", feed, usable, across, bevel, thickness, panels, max(loss, 0))
