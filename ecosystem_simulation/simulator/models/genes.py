from dataclasses import dataclass
from random import Random


@dataclass(slots=True)
class Genes:
    # Controls how hungry/aggressive a given specimen is, meaning
    # how quickly it will decide to hunt again after eating.
    # Values: [0, 1]
    appetite: float

    # lifespan * opts.max_age_in_ticks
    # Values: [0, 1]
    lifespan: float

    # maturity_age * opts.max_maturity_age
    # Values: [0, 1]
    maturity_age: float

    # gestation_age * opts.max_gestation_age
    # Values: [0, 1]
    gestation_age: float

    # Movement per tick
    # Values: [0, 1]
    speed: float

    # This gene controls how many children a single specimen will carry (fertility).
    # Values: [0, 1]
    min_children: float
    max_children: float

    # This gene controls how far the specimen can see.
    # Values: [0, 1]
    vision: float

    # This gene controls how quickly the `reproductive_urge` value
    # rises for a given specimen.
    # Values: [0, 1]
    reproductive_urge_quickness: float

    # Controls how timid specimen is (how quick to flee)
    # Values: [0, 1]
    timidity: float

    def mix(self, other: "Genes", rng: Random, mutation_chance: float, mutation_magnitude: float) -> "Genes":
        def mix_genes(x: float, y: float) -> float:
            final_gene = (x + y) / 2
            if rng.uniform(0, 1) < mutation_chance:
                final_gene += rng.gauss(mutation_magnitude, mutation_chance)
            return max(0.0, min(final_gene, 1.0))

        new_genes = Genes(
            appetite=mix_genes(self.appetite, other.appetite),
            lifespan=mix_genes(self.lifespan, other.lifespan),
            maturity_age=mix_genes(self.maturity_age, other.maturity_age),
            gestation_age=mix_genes(self.gestation_age, other.gestation_age),
            speed=mix_genes(self.speed, other.speed),
            min_children=mix_genes(self.min_children, other.min_children),
            max_children=mix_genes(self.max_children, other.max_children),
            vision=mix_genes(self.vision, other.vision),
            reproductive_urge_quickness=mix_genes(self.reproductive_urge_quickness, other.reproductive_urge_quickness),
            timidity=mix_genes(self.timidity, other.timidity)
        )
        new_genes.min_children = min(new_genes.min_children, new_genes.max_children)
        new_genes.max_children = max(new_genes.max_children, new_genes.max_children)
        return new_genes


