import random
from collections import defaultdict
from dataclasses import field, dataclass
from typing import Callable, Optional, cast

from .abc import SimulatorBackend, SimulatedTick
from .fuzzy_logic import determine_state_fuzzy, State
from .options import SimulationOptions, EntitySimulationOptions, LogicType
from .models import *
from sys import maxsize

class DraftSimulationState:
    grid_width: int
    grid_height: int
    entity_by_id: dict[int, Entity]

    predator_by_position: dict[tuple[int, int], list[Predator]]
    prey_by_position: dict[tuple[int, int], list[Prey]]
    food_by_position: dict[tuple[int, int], list[Food]]

    food_spawning_accumulator: float

    def __init__(self, grid_width: int, grid_height: int):
        self.grid_width = grid_width
        self.grid_height = grid_height

        self.entity_by_id = {}
        self.predator_by_position = defaultdict(list)
        self.prey_by_position = defaultdict(list)
        self.food_by_position = defaultdict(list)

        self.food_spawning_accumulator = 0

    def set_food_spawning_accumulator(self, value: float):
        self.food_spawning_accumulator = value

    def add_predator(self, predator: Predator):
        self.entity_by_id[predator.id] = predator
        self.predator_by_position[predator.position.to_tuple()].append(predator)

    def add_prey(self, prey: Prey):
        self.entity_by_id[prey.id] = prey
        self.prey_by_position[prey.position.to_tuple()].append(prey)

    def add_food(self, food: Food):
        self.entity_by_id[food.id] = food
        self.food_by_position[food.position.to_tuple()].append(food)

    def into_final_simulation_state(self) -> SimulationState:
        return SimulationState(
            grid_width=self.grid_width,
            grid_height=self.grid_height,
            entity_by_id=self.entity_by_id,
            predator_by_position=self.predator_by_position,
            prey_by_position=self.prey_by_position,
            food_by_position=self.food_by_position,
            food_spawning_accumulator=self.food_spawning_accumulator
        )



class EcosystemSimulator(SimulatorBackend):
    options: SimulationOptions
    _current_tick_number: int
    _current_state: SimulationState
    _on_tick: Optional[Callable[[SimulatedTick], None]]
    _rng: random.Random
    _entity_id_generator: int

    def __init__(self, options_: SimulationOptions):
        self.options = options_
        self._current_tick_number = 0
        self._on_tick = None
        self._rng = random.Random(x=options_.randomness_seed)
        self._entity_id_generator = 1
        self._current_state = self._prepare_initial_state()

    def next_simulation_tick(self) -> SimulatedTick:
        next_state = self._next_state()
        next_tick_number = self._current_tick_number + 1

        self._current_state = next_state
        self._current_tick_number = next_tick_number

        if self._on_tick is not None:
            self._on_tick(SimulatedTick(
                tick_number=next_tick_number,
                state=next_state
            ))

        return SimulatedTick(
            tick_number=next_tick_number,
            state=next_state
        )


    def _random_position(self) -> WorldPosition:
        return WorldPosition(
            x=self._rng.randint(0, self.options.world_width),
            y=self._rng.randint(0, self.options.world_height),
        )


    def _prepare_initial_state(self) -> SimulationState:
        opts = self.options

        new_state = DraftSimulationState(self.options.world_width, self.options.world_height)
        new_state.set_food_spawning_accumulator(0)

        def random_genes() -> Genes:
            return Genes(
                appetite=self._rng.uniform(0.2, 0.8),
                lifespan=self._rng.uniform(0.8, 1.0),
                maturity_age=self._rng.uniform(0.2, 0.6),
                gestation_age=self._rng.uniform(0.2, 0.6),
                speed=self._rng.uniform(0.1, 0.8),
                min_children=self._rng.uniform(0.1, 0.3),
                max_children=self._rng.uniform(0.4, 0.6),
                vision=self._rng.uniform(0.3, 0.6),
                reproductive_urge_quickness=self._rng.uniform(0.2, 0.8),
                timidity=self._rng.uniform(0.2, 0.8),
            )

        def spawn_args(pos: WorldPosition, satiation: float, genes: Genes):
            mature = self._rng.choice([True, False])
            reproductive_urge = 0
            if mature:
                reproductive_urge = self._rng.uniform(0, 0.5)
            pregnant = False
            pregnant_duration = 0
            if mature:
                pregnant = self._rng.choice([True, False])
                if pregnant:
                    pregnant_duration = self._rng.uniform(0, 1)
            return {
                'id': self._gen_entity_id(),
                'alive': True,
                'age_ticks': self._rng.randint(0, 80),
                'position': pos,
                'generation': 1,
                'state': None,
                'move_accum': self._rng.uniform(0, 1),
                'satiation': satiation,
                'reproductive_urge': reproductive_urge,
                'genes': genes,
                'mature': mature,
                'pregnant': pregnant,
                'pregnant_duration': pregnant_duration,
                'pregnant_partner_genes': genes,
            }

        for _ in range(opts.predator.initial_number):
            # Spawn the predator at a random position in the state.
            args = spawn_args(self._random_position(), opts.predator.initial_satiation_on_spawn, random_genes())
            predator = Predator(**args)
            new_state.add_predator(predator)

        for _ in range(opts.prey.initial_number):
            # Give the prey uniformly random genes in the configured range.
            args = spawn_args(self._random_position(), opts.predator.initial_satiation_on_spawn, random_genes())
            prey = Prey(**args)
            new_state.add_prey(prey)


        for _ in range(opts.initial_number_of_food_items):
            food = Food(
                id=self._gen_entity_id(),
                alive=True,
                age_ticks=self._rng.randint(0, opts.food_item_life_tick),
                max_age=opts.food_item_life_tick,
                position=self._random_position(),
            )
            new_state.add_food(food)

        return new_state.into_final_simulation_state()


    def _next_state(self) -> SimulationState:
        """
        Will perform a single simulation tick. Because we want to track changes
        over time, **THIS FUNCTION MUST NOT MUTATE `state`**, but instead return a new one!
        """

        world = self._current_state
        opts = self.options

        new_world = DraftSimulationState(opts.world_width, opts.world_height)

        def add_offsprings(c: Creature, entity_opts: EntitySimulationOptions):
            num_offsprings = round(self._rng.uniform(c.genes.min_children, c.genes.max_children) * entity_opts.max_children_per_birth)
            for _ in range(num_offsprings):
                mixed_gene = c.genes.mix(c.pregnant_partner_genes, self._rng, opts.child_gene_mutation_chance_when_mating, opts.child_gene_mutation_magnitude_when_mating)
                new_pos = WorldPosition(x=c.position.x + self._rng.randint(-1, 1), y=c.position.y + self._rng.randint(-1, 1))
                common_args = {
                    'id': self._gen_entity_id(),
                    'alive': True,
                    'age_ticks': 0,
                    'position': new_pos,
                    'generation': c.generation + 1,
                    'state': None,
                    'move_accum': 0.0,
                    'satiation': entity_opts.initial_satiation_on_spawn,
                    'reproductive_urge': 0.0,
                    'genes': mixed_gene,
                    'mature': False,
                    'pregnant': False,
                    'pregnant_duration': 0,
                    'pregnant_partner_genes': None,
                }
                if isinstance(c, Prey):
                    prey = Prey(**common_args)
                    new_world.add_prey(prey)
                elif isinstance(c, Predator):
                    predator = Predator(**common_args)
                    new_world.add_predator(predator)
                else:
                    assert False


        def creature_update(c: Creature, entity_opts: EntitySimulationOptions) -> bool:
            # Common logic
            c.satiation -= entity_opts.satiation_loss_per_tick
            if c.mature and not c.pregnant:
                c.reproductive_urge += c.genes.reproductive_urge_quickness
            elif c.age_ticks >= c.genes.maturity_age * entity_opts.max_juvenile_in_ticks:
                c.mature = True

            # Check gestation completion
            if c.pregnant:
                c.pregnant_duration += 1
            if c.pregnant and c.pregnant_duration > round(c.genes.gestation_age * entity_opts.max_gestation_in_ticks):
                add_offsprings(c, entity_opts)
                c.pregnant = False
                c.pregnant_duration = 0

            c.move_accum += c.genes.speed
            if c.move_accum < 1:
                return False
            c.move_accum -= 1
            return True


        def update_state(c: Creature, entity_opts: EntitySimulationOptions):
            state = c.state
            if isinstance(state, WanderingState):
                # Note: So entities wonder in somewhat similar direction (no back and forth)
                change_x = self._rng.choice([True, False])
                if change_x:
                    c.state.dir_x = max(-1, min(1, state.dir_x + self._rng.choice([-1, 0, 1])))
                else:
                    c.state.dir_y = max(-1, min(1, state.dir_y + self._rng.choice([-1, 0, 1])))

                new_x = c.position.x + c.state.dir_x
                new_y = c.position.y + c.state.dir_y
                if new_x < 0 or new_x >= opts.world_width:
                    c.state.dir_x = -c.state.dir_x
                if new_y < 0 or new_y >= opts.world_height:
                    c.state.dir_y = -c.state.dir_y

                c.position.x += c.state.dir_x
                c.position.y += c.state.dir_y
            elif isinstance(state, HuntState) or isinstance(state, MateState):
                # Move towards (same for both states)
                target = cast(Creature, world.entity_by_id[state.target_id])
                dir = c.position.direction_to(target.position)
                c.position.x += dir.x
                c.position.y += dir.y
                if c.position == target.position and isinstance(state, HuntState):
                    # Multiple hunters can share a meal
                    # Hunted
                    target.alive = False
                    c.satiation += entity_opts.satiation_per_feeding
                elif target.alive and c.position == target.position and isinstance(state, MateState):
                    # Mated
                    if not target.pregnant:
                        target.pregnant = True
                        target.pregnant_duration = 0
                        target.pregnant_partner_genes = c.genes
                        target.reproductive_urge = 0
                    c.reproductive_urge = 0



            elif isinstance(state, FleeState):
                # Move away
                dir = c.position.direction_to(world.entity_by_id[state.target_id].position)
                c.position.x -= dir.x
                c.position.y -= dir.y
            else:
                assert False

            c.position.x = min(max(0, c.position.x), opts.world_width - 1)
            c.position.y = min(max(0, c.position.y), opts.world_height - 1)

        def determine_creature_state_fuzzy(_creature: Creature, vision) -> any:
            """
            Common logic for determining next creature state.
            """
            if isinstance(_creature, Prey):
                food_iterator = world.iter_nearby_food(_creature.position, vision)
                mate_iterator = world.iter_nearby_prey(_creature.position, vision)
            else:
                food_iterator = world.iter_nearby_prey(_creature.position, vision)
                mate_iterator = world.iter_nearby_predator(_creature.position, vision)

            # Get the closest food and mate
            closest_food_id = None
            food_dst = maxsize
            for food in food_iterator:
                dst = _creature.position.distance_from(food.position)
                if dst < food_dst:
                    closest_food_id = food.id
                    food_dst = dst

            closest_mate_id = None
            mate_dst = maxsize
            for mate in mate_iterator:
                if mate == _creature:
                    continue
                if not mate.mature or mate.pregnant:
                    continue
                dst = _creature.position.distance_from(mate.position)
                if dst < mate_dst:
                    closest_mate_id = mate.id
                    mate_dst = dst

            _new_state = determine_state_fuzzy(_creature, vision, food_dst, mate_dst)

            # In case the creature wants to mate or eat food without having a nearby target
            # (If the fuzzy logic is correctly constructed this should not occur)
            if _new_state == State.FOOD and not closest_food_id or \
                _new_state == State.REPRODUCTION and not closest_mate_id:
                return WanderingState(self._rng.randint(-1, 1), self._rng.randint(-1, 1))

            if _new_state == State.FOOD:
                return HuntState(closest_food_id)
            elif _new_state == State.REPRODUCTION:
                return MateState(closest_mate_id)
            else:
                return WanderingState(self._rng.randint(-1, 1), self._rng.randint(-1, 1))


        def determine_prey_state(prey: Prey, logic: LogicType) -> EntityState:
            vision = round(prey.genes.vision * opts.max_vision_distance)

            if logic == LogicType.FUZZY:
                return determine_creature_state_fuzzy(prey, vision)

            # Check flee first (highest priority for survival)
            closest_pred = None
            pred_dst = opts.world_width * opts.world_height
            for pred in world.iter_nearby_predator(prey.position, vision):
                dst = prey.position.distance_from(pred.position)
                if dst < pred_dst:
                    closest_pred = pred
                    pred_dst = dst
            if closest_pred is not None:
                flee_threshold = prey.genes.timidity * (1 / max(1, pred_dst))
                #print(pred_dst, (1 / max(1, pred_dst)))
                if flee_threshold > 0.2: # Arbitrary (maybe put in options?)
                    return FleeState(target_id=prey.id)

            # Check hunting (when hungry)
            if prey.satiation < prey.genes.appetite:
                closest_food = None
                food_dst = opts.world_width * opts.world_height
                for food in world.iter_nearby_food(prey.position, vision):
                    dst = prey.position.distance_from(food.position)
                    if dst < food_dst:
                        closest_food = food
                        food_dst = dst
                if closest_food is not None:
                    return HuntState(closest_food.id)

            # Check mating (only when mature, not hungry, not already pregnant and horny)
            if prey.satiation > 0.2 and prey.mature and not prey.pregnant and prey.reproductive_urge > 1.0:
                closest_mate = None
                mate_dst = opts.world_width * opts.world_height
                for mate in world.iter_nearby_prey(prey.position, vision):
                    if mate == prey:
                        continue
                    if not mate.mature or mate.pregnant:
                        continue
                    dst = prey.position.distance_from(mate.position)
                    if dst < mate_dst:
                        closest_mate = mate
                        mate_dst = dst
                if closest_mate is not None:
                    return MateState(closest_mate.id)

            # Wander
            return WanderingState(self._rng.randint(-1, 1), self._rng.randint(-1, 1))

        def determine_predator_state(pred: Predator, logic: LogicType) -> EntityState:
            vision = round(pred.genes.vision * opts.max_vision_distance)

            if logic == LogicType.FUZZY:
                return determine_creature_state_fuzzy(pred, vision)


            # No need to flee
            # Check hunting (when hungry)
            if pred.satiation < pred.genes.appetite:
                closest_food = None
                food_dst = opts.world_width * opts.world_height
                for food in world.iter_nearby_prey(pred.position, vision):
                    dst = pred.position.distance_from(food.position)
                    if dst < food_dst:
                        closest_food = food
                        food_dst = dst
                if closest_food is not None:
                    return HuntState(closest_food.id)

            # Check mating
            if pred.satiation > 0.2 and pred.mature and not pred.pregnant  and pred.reproductive_urge > 1.0:
                closest_mate = None
                mate_dst = opts.world_width * opts.world_height
                for mate in world.iter_nearby_predator(pred.position, vision):
                    if mate == pred:
                        continue
                    if not mate.mature or mate.pregnant:
                        continue
                    dst = pred.position.distance_from(mate.position)
                    if dst < mate_dst:
                        closest_mate = mate
                        mate_dst = dst
                if closest_mate is not None:
                    return MateState(closest_mate.id)

            # Default state (Wander)
            return WanderingState(self._rng.randint(-1, 1), self._rng.randint(-1, 1))


        def check_creature_aliveness(c: Creature, max_age: int):
            c.age_ticks += 1
            if c.age_ticks >= round(c.genes.lifespan * max_age):
                c.alive = False
            if c.satiation <= 0:
                c.alive = False

        # END HELPER FUNCTIONS FOR NEXT STATE #########################################################################

        # Process all predators
        for predator in list(world.predators()):
            if not predator.alive:
                continue
            if not creature_update(predator, opts.predator):
                continue

            new_state = determine_predator_state(predator, opts.logic_determine_creature_state)
            if not (isinstance(new_state, WanderingState) and isinstance(predator.state, WanderingState)):
                # Note: WanderingState should remain the same...
                predator.state = new_state

            update_state(predator, opts.predator)
            check_creature_aliveness(predator, opts.predator.max_age_in_ticks)

        # Process all prey
        for prey in list(world.prey()):
            if not prey.alive:
                continue
            if not creature_update(prey, opts.prey):
                continue

            new_state = determine_prey_state(prey, opts.logic_determine_creature_state)
            if not (isinstance(new_state, WanderingState) and isinstance(prey.state, WanderingState)):
                # Note: WanderingState should remain the same...
                prey.state = new_state

            update_state(prey, opts.prey)
            check_creature_aliveness(prey, opts.prey.max_age_in_ticks)

        # Overcrowding (no more than two entities can present on the same place)
        for _, values in world.prey_by_position.items():
            if len(values) >= 3:
                values[0].alive = False
        for _, values in world.predator_by_position.items():
            if len(values) >= 3:
                values[0].alive = False

        # Update food age ticks
        for food in world.food():
            food.age_ticks += 1
            if food.age_ticks >= opts.food_item_life_tick:
                food.alive = False

        # Copy all old entities to the new state
        for entity in world.iter_entities():
            if not entity.alive:
                continue
            if isinstance(entity, Food):
                new_world.add_food(entity)
            elif isinstance(entity, Prey):
                new_world.add_prey(entity)
            elif isinstance(entity, Predator):
                new_world.add_predator(entity)
            else:
                assert False

        # Spawns some additional food based on the spawning rate.
        new_food_spawning_accumulator = world.food_spawning_accumulator + self.options.food_item_spawning_rate_per_tick
        food_count = self._current_state.food_count()

        while food_count < self.options.max_number_of_food_items and new_food_spawning_accumulator >= 1.0:
            new_world.add_food(Food(
                id=self._gen_entity_id(),
                alive=True,
                age_ticks=0,
                max_age=self.options.food_item_life_tick,
                position=self._random_position()
            ))
            new_food_spawning_accumulator -= 1.0

        new_world.set_food_spawning_accumulator(new_food_spawning_accumulator)

        return new_world.into_final_simulation_state()

    def _gen_entity_id(self):
        self._entity_id_generator += 1
        return self._entity_id_generator